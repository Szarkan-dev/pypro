"""
Automated Unit Test Suite for Simple Reminder List Application.

Verifies model behavior, defensive input validation, storage DAO persistence,
corrupt-file auto-recovery, analytics engine, structured logging, generator streaming,
pagination, file locking, and report exports.
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Reminder, Priority, Category, ReminderStatus
from src.validation import InputValidator, ValidationError
from src.storage import ReminderDAO, StorageError, file_lock, LockError
from src.analytics import ReminderAnalytics
from src.logger import setup_logger


class TestReminderModel(unittest.TestCase):
    """Test suite for domain model methods and date arithmetic."""

    def test_model_instantiation_and_serialization(self):
        r = Reminder(
            id=1,
            title="Test Reminder",
            category="Work",
            due_date="2026-12-01 17:00",
            priority="High",
            description="Sample description",
            status="Pending"
        )
        self.assertEqual(r.id, 1)
        self.assertEqual(r.title, "Test Reminder")
        d = r.to_dict()
        self.assertEqual(d["title"], "Test Reminder")

        r2 = Reminder.from_dict(d)
        self.assertEqual(r2.id, r.id)
        self.assertEqual(r2.due_date, r.due_date)

    def test_date_parsing_formats(self):
        r1 = Reminder(id=1, title="Date Test 1", category="Work", due_date="2026-12-01")
        dt1 = r1.parse_due_date()
        self.assertEqual(dt1.year, 2026)
        self.assertEqual(dt1.hour, 23)

        r2 = Reminder(id=2, title="Date Test 2", category="Work", due_date="2026-12-01 14:30")
        dt2 = r2.parse_due_date()
        self.assertEqual(dt2.hour, 14)
        self.assertEqual(dt2.minute, 30)

    def test_overdue_and_upcoming_logic(self):
        ref = datetime(2026, 11, 18, 12, 0, 0)

        # Overdue item
        r_overdue = Reminder(id=1, title="Past Item", category="Work", due_date="2026-11-10 10:00", status="Pending")
        self.assertTrue(r_overdue.is_overdue(ref))
        self.assertFalse(r_overdue.is_upcoming(7, ref))

        # Upcoming item (in 3 days)
        r_upcoming = Reminder(id=2, title="Upcoming Item", category="Work", due_date="2026-11-21 10:00", status="Pending")
        self.assertFalse(r_upcoming.is_overdue(ref))
        self.assertTrue(r_upcoming.is_upcoming(7, ref))

        # Completed item past due date should not be marked overdue
        r_completed = Reminder(id=3, title="Completed Past Item", category="Work", due_date="2026-11-10 10:00", status="Completed")
        self.assertFalse(r_completed.is_overdue(ref))

    def test_urgency_score_ranking(self):
        ref = datetime(2026, 11, 18, 12, 0, 0)
        r_low = Reminder(id=1, title="Low Prio Future", category="Work", due_date="2026-11-25 12:00", priority="Low")
        r_high = Reminder(id=2, title="High Prio Future", category="Work", due_date="2026-11-25 12:00", priority="High")
        r_overdue = Reminder(id=3, title="Overdue Item", category="Work", due_date="2026-11-15 12:00", priority="Medium")

        score_low = r_low.urgency_score(ref)
        score_high = r_high.urgency_score(ref)
        score_overdue = r_overdue.urgency_score(ref)

        self.assertGreater(score_high, score_low)
        self.assertGreater(score_overdue, score_high)


class TestInputValidator(unittest.TestCase):
    """Test suite for defensive input validation routines."""

    def test_title_validation(self):
        self.assertEqual(InputValidator.validate_title("Valid Title"), "Valid Title")
        with self.assertRaises(ValidationError):
            InputValidator.validate_title("   ")
        with self.assertRaises(ValidationError):
            InputValidator.validate_title("A")  # Too short

    def test_date_validation(self):
        self.assertEqual(InputValidator.validate_date("2026-12-31"), "2026-12-31")
        self.assertEqual(InputValidator.validate_date("2026-12-31 18:00"), "2026-12-31 18:00")

        # Invalid format
        with self.assertRaises(ValidationError):
            InputValidator.validate_date("31/12/2026")

        # Invalid calendar date (Feb 31)
        with self.assertRaises(ValidationError):
            InputValidator.validate_date("2026-02-31")

        # Out of bounds year
        with self.assertRaises(ValidationError):
            InputValidator.validate_date("1995-01-01")

    def test_priority_validation(self):
        self.assertEqual(InputValidator.validate_priority("high"), "High")
        self.assertEqual(InputValidator.validate_priority("CRITICAL"), "Critical")
        with self.assertRaises(ValidationError):
            InputValidator.validate_priority("Extreme")

    def test_category_validation(self):
        self.assertEqual(InputValidator.validate_category("work"), "Work")
        self.assertEqual(InputValidator.validate_category("custom_tag"), "Custom_tag")


class TestReminderDAO(unittest.TestCase):
    """Test suite for Data Access Object storage, file locking, and streaming."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.temp_dir, "test_reminders.json")
        self.csv_file = os.path.join(self.temp_dir, "test_reminders.csv")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_json_crud_operations(self):
        dao = ReminderDAO(self.json_file)
        self.assertEqual(len(dao.load_all()), 0)

        # Add
        r = Reminder(id=0, title="DAO Test Item", category="Work", due_date="2026-12-10 12:00")
        added = dao.add(r)
        self.assertEqual(added.id, 1)
        self.assertEqual(len(dao.load_all()), 1)

        # Get by ID
        fetched = dao.get_by_id(1)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "DAO Test Item")

        # Update
        fetched.status = ReminderStatus.COMPLETED.value
        self.assertTrue(dao.update(fetched))
        updated = dao.get_by_id(1)
        self.assertEqual(updated.status, ReminderStatus.COMPLETED.value)

        # Delete
        self.assertTrue(dao.delete(1))
        self.assertEqual(len(dao.load_all()), 0)

    def test_corrupted_json_recovery(self):
        with open(self.json_file, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON DATA CORRUPTED !!!")

        dao = ReminderDAO(self.json_file)
        items = dao.load_all()
        self.assertEqual(len(items), 0)
        self.assertTrue(Path(self.json_file).exists())

    def test_csv_persistence(self):
        dao = ReminderDAO(self.csv_file)
        r = Reminder(id=1, title="CSV Test Item", category="Academic", due_date="2026-11-20 10:00")
        dao.add(r)

        items = dao.load_all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "CSV Test Item")

    def test_generator_streaming(self):
        dao = ReminderDAO(self.json_file)
        for i in range(1, 6):
            dao.add(Reminder(id=0, title=f"Stream Item #{i}", category="Work", due_date="2026-12-01"))

        # Verify generator streaming yields records sequentially
        stream = dao.stream_all()
        items = list(stream)
        self.assertEqual(len(items), 5)
        self.assertEqual(items[0].title, "Stream Item #1")

    def test_pagination(self):
        dao = ReminderDAO(self.json_file)
        for i in range(1, 15):
            dao.add(Reminder(id=0, title=f"Task #{i}", category="Work" if i % 2 == 0 else "Finance", due_date="2026-12-01"))

        # Fetch page 1 (size 5)
        page1, total, pages = dao.get_paginated(page=1, page_size=5)
        self.assertEqual(len(page1), 5)
        self.assertEqual(total, 14)
        self.assertEqual(pages, 3)

        # Filtered pagination
        p_fin, fin_total, fin_pages = dao.get_paginated(page=1, page_size=5, category="Finance")
        self.assertEqual(fin_total, 7)

    def test_concurrent_file_locking(self):
        target_path = Path(self.json_file)
        target_path.touch()

        # Test normal lock acquisition and release
        with file_lock(target_path):
            lock_path = target_path.with_suffix(target_path.suffix + ".lock")
            self.assertTrue(lock_path.exists())

        # Verify lock file is cleaned up after context block
        self.assertFalse(lock_path.exists())


class TestSystemLogging(unittest.TestCase):
    """Test suite for structured logging initialization and audit trail."""

    def test_structured_logging(self):
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "test_app.log")

        logger = setup_logger("TestLogger", log_file=log_file)
        logger.info("Test log entry message.")

        self.assertTrue(Path(log_file).exists())
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Test log entry message.", content)
        self.assertIn("[INFO]", content)

        shutil.rmtree(temp_dir, ignore_errors=True)


class TestReminderAnalytics(unittest.TestCase):
    """Test suite for analytics calculations, filtering, and report exports."""

    def test_summary_metrics(self):
        ref = datetime(2026, 11, 18, 12, 0, 0)
        reminders = [
            Reminder(id=1, title="Past Item", category="Work", due_date="2026-11-10 10:00", status="Pending"),
            Reminder(id=2, title="Upcoming Item", category="Work", due_date="2026-11-20 10:00", status="Pending"),
            Reminder(id=3, title="Completed Item", category="Personal", due_date="2026-11-15 10:00", status="Completed"),
        ]

        metrics = ReminderAnalytics.generate_summary_metrics(reminders, ref)
        self.assertEqual(metrics["total_records"], 3)
        self.assertEqual(metrics["pending_count"], 2)
        self.assertEqual(metrics["completed_count"], 1)
        self.assertEqual(metrics["overdue_count"], 1)
        self.assertEqual(metrics["upcoming_7d_count"], 1)
        self.assertEqual(metrics["completion_rate_pct"], 33.3)

    def test_filtering_engine(self):
        reminders = [
            Reminder(id=1, title="Buy Milk", category="Personal", due_date="2026-11-20 10:00", priority="Low"),
            Reminder(id=2, title="Submit Tax Form", category="Finance", due_date="2026-11-22 10:00", priority="High"),
            Reminder(id=3, title="Tax Audit Review", category="Finance", due_date="2026-11-25 10:00", priority="Critical"),
        ]

        res1 = ReminderAnalytics.filter_reminders(reminders, keyword="Tax")
        self.assertEqual(len(res1), 2)

        res2 = ReminderAnalytics.filter_reminders(reminders, category="Finance", priority="Critical")
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0].id, 3)

    def test_markdown_report_generation(self):
        temp_dir = tempfile.mkdtemp()
        report_file = os.path.join(temp_dir, "test_report.md")

        reminders = [
            Reminder(id=1, title="Sample Task", category="Work", due_date="2026-11-20 10:00", priority="High")
        ]

        out_path = ReminderAnalytics.export_markdown_report(reminders, report_file)
        self.assertTrue(out_path.exists())

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Simple Reminder List — Executive Audit Report", content)
        self.assertIn("KPI Metrics Summary", content)

        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
