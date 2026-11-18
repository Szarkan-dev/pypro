#!/usr/bin/env python3
"""
Simple Reminder List Application — FutureReady Hack (Project #109)
Main Application Launcher & Entry Point.

Usage:
    python main.py             # Launch interactive console UI
    python main.py --seed      # Reset and re-seed dataset with 36 sample entries
    python main.py --test      # Run automated system unit test suite
    python main.py --export    # Generate Markdown audit summary report
"""

import sys
import os
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.logger import setup_logger, logger
from src.cli import ConsoleUI
from src.storage import ReminderDAO
from src.analytics import ReminderAnalytics
from generate_seed_data import generate_seed


def main():
    setup_logger("SimpleReminder", log_file="logs/app.log")
    logger.info("Starting Simple Reminder List Application...")
    args = sys.argv[1:]

    if "--seed" in args:
        print("🌱 Generating fresh seed dataset...")
        logger.info("Executing dataset seed routine...")
        generate_seed()
        print("Done!")
        sys.exit(0)

    if "--test" in args:
        print("🧪 Executing system diagnostic test suite...")
        logger.info("Executing diagnostic test suite...")
        import unittest
        loader = unittest.TestLoader()
        tests_dir = os.path.join(os.path.dirname(__file__), "tests")
        suite = loader.discover(start_dir=tests_dir, pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    if "--export" in args:
        print("📄 Exporting executive report...")
        logger.info("Executing executive report export...")
        dao = ReminderDAO("data/reminders.json")
        reminders = dao.load_all()
        out_path = ReminderAnalytics.export_markdown_report(reminders)
        print(f"Exported report to: {out_path.resolve()}")
        sys.exit(0)

    # Default interactive UI
    app = ConsoleUI("data/reminders.json")
    app.run()


if __name__ == "__main__":
    main()
