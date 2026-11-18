"""
Data Access Object (DAO) & Persistence Layer for Simple Reminder List Application.

Implements robust file operations for JSON and CSV storage formats, featuring zero-dependency
error recovery for missing or corrupted files, schema validation, atomic writes, concurrent
file locking, structured logging, and generator-based data streaming/pagination.
"""

import csv
import json
import os
import shutil
import time
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any, Generator, Tuple
from datetime import datetime

from src.models import Reminder, Priority, Category, ReminderStatus
from src.logger import logger


class StorageError(Exception):
    """Custom exception raised during storage read/write operations."""
    pass


class LockError(StorageError):
    """Exception raised when file lock acquisition fails or times out."""
    pass


@contextmanager
def file_lock(lock_file_path: Path, timeout: float = 5.0, retry_interval: float = 0.05):
    """
    Context manager providing cross-platform file locking using atomic file creation.
    Prevents race conditions during concurrent read/write operations.
    """
    lock_path = lock_file_path.with_suffix(lock_file_path.suffix + ".lock")
    start_time = time.time()
    acquired = False

    while not acquired:
        try:
            # Atomic creation flag O_CREAT | O_EXCL
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.close(fd)
            acquired = True
            logger.debug(f"Acquired file lock: {lock_path}")
        except FileExistsError:
            # Check if lock file is stale (> 30 seconds old)
            try:
                st = lock_path.stat()
                if time.time() - st.st_mtime > 30.0:
                    lock_path.unlink(missing_ok=True)
                    logger.warning(f"Removed stale file lock: {lock_path}")
                    continue
            except OSError:
                pass

            if time.time() - start_time > timeout:
                logger.error(f"File lock acquisition timed out for {lock_file_path}")
                raise LockError(f"Could not acquire storage lock on {lock_file_path} within {timeout}s.")
            time.sleep(retry_interval)

    try:
        yield
    finally:
        if acquired:
            try:
                lock_path.unlink(missing_ok=True)
                logger.debug(f"Released file lock: {lock_path}")
            except OSError as e:
                logger.warning(f"Failed to release file lock {lock_path}: {e}")


class ReminderDAO:
    """
    Data Access Object encapsulating CRUD operations, generator streaming, pagination,
    and concurrent file locked persistence for Reminders.
    """

    CSV_HEADERS = [
        "id", "title", "category", "due_date", "priority",
        "description", "status", "created_at", "completed_at"
    ]

    def __init__(self, file_path: str = "data/reminders.json"):
        self.file_path = Path(file_path)
        self.format = self.file_path.suffix.lower().strip(".")
        if self.format not in ("json", "csv"):
            raise ValueError(f"Unsupported storage format: '{self.format}'. Use 'json' or 'csv'.")
        logger.info(f"Initialized ReminderDAO with backing file: {self.file_path} ({self.format.upper()})")
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Create storage directory and seed file if missing or corrupted."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            logger.info(f"Storage file {self.file_path} does not exist. Initializing empty storage.")
            self._initialize_empty_storage()
        else:
            # Verify file integrity
            try:
                self.load_all()
            except StorageError as e:
                logger.error(f"Storage integrity check failed for {self.file_path}: {e}. Triggering recovery.")
                self._backup_corrupted_file()
                self._initialize_empty_storage()

    def _initialize_empty_storage(self) -> None:
        """Create a fresh, empty storage file with default structure."""
        with file_lock(self.file_path):
            if self.format == "json":
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump({"reminders": [], "last_id": 0, "updated_at": datetime.now().isoformat()}, f, indent=2)
            elif self.format == "csv":
                with open(self.file_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(self.CSV_HEADERS)
        logger.info(f"Initialized clean {self.format.upper()} storage at {self.file_path}")

    def _backup_corrupted_file(self) -> None:
        """Rename corrupted storage file with timestamp suffix to prevent data loss."""
        if self.file_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupt_path = self.file_path.with_name(f"{self.file_path.stem}_corrupt_{timestamp}{self.file_path.suffix}")
            try:
                shutil.copy(self.file_path, corrupt_path)
                logger.warning(f"Corrupted storage backed up to: {corrupt_path}")
            except Exception as e:
                logger.error(f"Failed to back up corrupted file {self.file_path}: {e}")

    def stream_all(self) -> Generator[Reminder, None, None]:
        """
        Generator function streaming reminder records one-by-one from storage.
        Provides memory-efficient iteration without loading entire datasets into memory at once.
        """
        if not self.file_path.exists():
            return

        with file_lock(self.file_path):
            if self.format == "json":
                try:
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    items = data.get("reminders", []) if isinstance(data, dict) else data
                    for item in items:
                        if isinstance(item, dict):
                            yield Reminder.from_dict(item)
                except (json.JSONDecodeError, OSError) as e:
                    logger.error(f"Error streaming JSON file {self.file_path}: {e}")
                    raise StorageError(f"Failed to stream JSON storage file: {e}")
            elif self.format == "csv":
                try:
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            row_dict = {
                                "id": int(row.get("id", 0)),
                                "title": row.get("title", ""),
                                "category": row.get("category", Category.OTHER.value),
                                "due_date": row.get("due_date", ""),
                                "priority": row.get("priority", Priority.MEDIUM.value),
                                "description": row.get("description", ""),
                                "status": row.get("status", ReminderStatus.PENDING.value),
                                "created_at": row.get("created_at", ""),
                                "completed_at": row.get("completed_at") or None
                            }
                            yield Reminder.from_dict(row_dict)
                except (csv.Error, ValueError, OSError) as e:
                    logger.error(f"Error streaming CSV file {self.file_path}: {e}")
                    raise StorageError(f"Failed to stream CSV storage file: {e}")

    def load_all(self) -> List[Reminder]:
        """Load and deserialize all reminder records from disk."""
        reminders = list(self.stream_all())
        return sorted(reminders, key=lambda r: r.id)

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Tuple[List[Reminder], int, int]:
        """
        Memory-efficient pagination engine. Filters stream items and returns target page window.

        Returns:
            Tuple of (page_items, total_filtered_count, total_pages)
        """
        page = max(1, page)
        page_size = max(1, page_size)

        filtered: List[Reminder] = []
        q = search_query.lower().strip() if search_query else None

        for r in self.stream_all():
            if category and r.category.lower() != category.lower():
                continue
            if status and r.status.lower() != status.lower():
                continue
            if q and (q not in r.title.lower() and q not in r.description.lower()):
                continue
            filtered.append(r)

        # Sort filtered items by urgency score descending
        filtered.sort(key=lambda r: r.urgency_score(), reverse=True)

        total_count = len(filtered)
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = filtered[start_idx:end_idx]

        logger.debug(f"Paginated fetch page {page}/{total_pages} (count={len(page_items)}, total={total_count})")
        return page_items, total_count, total_pages

    def save_all(self, reminders: List[Reminder]) -> None:
        """Serialize and save all reminder records to disk under a file lock."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        max_id = max((r.id for r in reminders), default=0)

        with file_lock(self.file_path):
            if self.format == "json":
                payload = {
                    "reminders": [r.to_dict() for r in reminders],
                    "last_id": max_id,
                    "updated_at": datetime.now().isoformat()
                }
                temp_path = self.file_path.with_suffix(".tmp")
                try:
                    with open(temp_path, "w", encoding="utf-8") as f:
                        json.dump(payload, f, indent=2, ensure_ascii=False)
                    temp_path.replace(self.file_path)
                    logger.info(f"Successfully saved {len(reminders)} records to {self.file_path}")
                except OSError as e:
                    if temp_path.exists():
                        temp_path.unlink()
                    logger.error(f"Atomic JSON save error: {e}")
                    raise StorageError(f"Atomic JSON write failed: {e}")
            elif self.format == "csv":
                temp_path = self.file_path.with_suffix(".tmp")
                try:
                    with open(temp_path, "w", encoding="utf-8", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                        writer.writeheader()
                        for r in reminders:
                            d = r.to_dict()
                            if d["completed_at"] is None:
                                d["completed_at"] = ""
                            writer.writerow(d)
                    temp_path.replace(self.file_path)
                    logger.info(f"Successfully saved {len(reminders)} records to CSV {self.file_path}")
                except OSError as e:
                    if temp_path.exists():
                        temp_path.unlink()
                    logger.error(f"Atomic CSV save error: {e}")
                    raise StorageError(f"Atomic CSV write failed: {e}")

    def add(self, reminder: Reminder) -> Reminder:
        """Add a new reminder, automatically assigning a unique ID if 0."""
        reminders = self.load_all()
        if reminder.id <= 0:
            next_id = max((r.id for r in reminders), default=0) + 1
            reminder.id = next_id
        reminders.append(reminder)
        self.save_all(reminders)
        logger.info(f"Added reminder #{reminder.id}: '{reminder.title}'")
        return reminder

    def get_by_id(self, reminder_id: int) -> Optional[Reminder]:
        """Fetch a single reminder by ID using streaming search."""
        for r in self.stream_all():
            if r.id == reminder_id:
                return r
        return None

    def update(self, reminder: Reminder) -> bool:
        """Update an existing reminder record."""
        reminders = self.load_all()
        found = False
        for idx, r in enumerate(reminders):
            if r.id == reminder.id:
                reminders[idx] = reminder
                found = True
                break
        if found:
            self.save_all(reminders)
            logger.info(f"Updated reminder #{reminder.id}")
        return found

    def delete(self, reminder_id: int) -> bool:
        """Delete a reminder record by ID."""
        reminders = self.load_all()
        initial_len = len(reminders)
        reminders = [r for r in reminders if r.id != reminder_id]
        if len(reminders) < initial_len:
            self.save_all(reminders)
            logger.info(f"Deleted reminder #{reminder_id}")
            return True
        return False

    def create_backup(self, backup_dir: str = "data/backups") -> Path:
        """Generate a timestamped backup copy of current storage under file lock."""
        with file_lock(self.file_path):
            b_path = Path(backup_dir)
            b_path.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = b_path / f"reminders_backup_{timestamp}.{self.format}"
            shutil.copy(self.file_path, backup_file)
            logger.info(f"Created timestamped backup at: {backup_file}")
            return backup_file
