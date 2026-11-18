"""
Domain Data Models for Simple Reminder List Application.

Defines the core entity structures, enums, and computational methods for reminder state,
urgency calculations, and status tracking.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, date
from enum import Enum
from typing import Dict, Any, Optional


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Category(str, Enum):
    WORK = "Work"
    PERSONAL = "Personal"
    ACADEMIC = "Academic"
    FINANCE = "Finance"
    HEALTH = "Health"
    OTHER = "Other"


class ReminderStatus(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


@dataclass
class Reminder:
    id: int
    title: str
    category: str
    due_date: str  # Format: YYYY-MM-DD or YYYY-MM-DD HH:MM
    priority: str = Priority.MEDIUM.value
    description: str = ""
    status: str = ReminderStatus.PENDING.value
    created_at: str = ""
    completed_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def parse_due_date(self) -> datetime:
        """Parse due_date string into a naive datetime object."""
        date_str = self.due_date.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                if fmt == "%Y-%m-%d":
                    # Default due time to end of day
                    dt = dt.replace(hour=23, minute=59, second=59)
                return dt
            except ValueError:
                continue
        raise ValueError(f"Invalid date format: '{self.due_date}'. Expected YYYY-MM-DD or YYYY-MM-DD HH:MM")

    def is_overdue(self, reference_dt: Optional[datetime] = None) -> bool:
        """Check if reminder is past due date and still pending."""
        if self.status != ReminderStatus.PENDING.value:
            return False
        ref = reference_dt or datetime.now()
        return self.parse_due_date() < ref

    def is_upcoming(self, days: int = 7, reference_dt: Optional[datetime] = None) -> bool:
        """Check if reminder due date falls within the next N days and is pending."""
        if self.status != ReminderStatus.PENDING.value:
            return False
        ref = reference_dt or datetime.now()
        due_dt = self.parse_due_date()
        if due_dt < ref:
            return False  # Overdue items are categorized separately
        delta_days = (due_dt - ref).total_seconds() / 86400.0
        return delta_days <= days

    def days_remaining(self, reference_dt: Optional[datetime] = None) -> int:
        """Return remaining days until due date (negative if overdue)."""
        ref = reference_dt or datetime.now()
        due_dt = self.parse_due_date()
        delta = due_dt - ref
        return delta.days

    def urgency_score(self, reference_dt: Optional[datetime] = None) -> float:
        """
        Compute an urgency heuristic score.
        Higher score indicates higher priority for sorting.
        Overdue items get highest weight, followed by Priority weight and proximity to deadline.
        """
        ref = reference_dt or datetime.now()
        due_dt = self.parse_due_date()
        hours_diff = (due_dt - ref).total_seconds() / 3600.0

        priority_weights = {
            Priority.CRITICAL.value: 100.0,
            Priority.HIGH.value: 75.0,
            Priority.MEDIUM.value: 50.0,
            Priority.LOW.value: 25.0
        }
        p_weight = priority_weights.get(self.priority, 50.0)

        if hours_diff < 0:
            # Overdue item: baseline 1000 + magnitude of overdue hours
            return 1000.0 + abs(hours_diff) + p_weight
        else:
            # Future item: weight inversely proportional to remaining hours
            proximity = 1000.0 / (hours_diff + 1.0)
            return p_weight + proximity

    def to_dict(self) -> Dict[str, Any]:
        """Serialize reminder instance to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reminder":
        """Instantiate a Reminder from dictionary data with defensive defaults."""
        return cls(
            id=int(data.get("id", 0)),
            title=str(data.get("title", "")).strip(),
            category=str(data.get("category", Category.OTHER.value)).strip(),
            due_date=str(data.get("due_date", "")).strip(),
            priority=str(data.get("priority", Priority.MEDIUM.value)).strip(),
            description=str(data.get("description", "")).strip(),
            status=str(data.get("status", ReminderStatus.PENDING.value)).strip(),
            created_at=str(data.get("created_at", "")).strip(),
            completed_at=data.get("completed_at")
        )
