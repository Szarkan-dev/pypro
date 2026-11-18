"""
Defensive Input Validation & Sanitization Module.

Provides centralized validation functions, regex sanitizers, and console input loops
to prevent crashes from non-conforming types, missing dates, or bad formats.
"""

import re
from datetime import datetime
from typing import Optional, Tuple

from src.models import Priority, Category, ReminderStatus


class ValidationError(Exception):
    """Custom exception raised when user input fails business rule validation."""
    pass


class InputValidator:
    """Centralized validator for reminder attributes and console prompt inputs."""

    DATE_PATTERNS = [
        (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "%Y-%m-%d"),
        (re.compile(r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}$"), "%Y-%m-%d %H:%M"),
        (re.compile(r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$"), "%Y-%m-%d %H:%M:%S"),
    ]

    @classmethod
    def sanitize_string(cls, input_str: str, max_length: int = 255, allow_empty: bool = False) -> str:
        """Sanitize raw text input by stripping whitespace and neutralizing control characters."""
        if input_str is None:
            if allow_empty:
                return ""
            raise ValidationError("Input cannot be None.")

        # Remove control characters except newline/tab
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", str(input_str)).strip()

        if not allow_empty and not sanitized:
            raise ValidationError("Input cannot be blank or empty whitespace.")

        if len(sanitized) > max_length:
            raise ValidationError(f"Input exceeds maximum allowed length of {max_length} characters.")

        return sanitized

    @classmethod
    def validate_title(cls, title: str) -> str:
        """Validate reminder title."""
        clean_title = cls.sanitize_string(title, max_length=100, allow_empty=False)
        if len(clean_title) < 2:
            raise ValidationError("Title must be at least 2 characters long.")
        return clean_title

    @classmethod
    def validate_date(cls, date_str: str, allow_past: bool = True) -> str:
        """
        Validate date format (YYYY-MM-DD or YYYY-MM-DD HH:MM).
        Ensures calendar validity (e.g. rejects Feb 31 or invalid leap years).
        """
        clean_date = cls.sanitize_string(date_str, max_length=20, allow_empty=False)

        parsed_dt: Optional[datetime] = None
        matched_format: Optional[str] = None

        for pattern, fmt in cls.DATE_PATTERNS:
            if pattern.match(clean_date):
                try:
                    parsed_dt = datetime.strptime(clean_date, fmt)
                    matched_format = fmt
                    break
                except ValueError as e:
                    raise ValidationError(f"Invalid calendar date '{clean_date}': {e}")

        if parsed_dt is None:
            raise ValidationError(
                f"Date '{clean_date}' does not match required format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM"
            )

        # Logical bounds check: reasonable year range (2000 to 2100)
        if parsed_dt.year < 2000 or parsed_dt.year > 2100:
            raise ValidationError(f"Year {parsed_dt.year} is outside allowable bounds (2000-2100).")

        return parsed_dt.strftime(matched_format)

    @classmethod
    def validate_priority(cls, priority_str: str) -> str:
        """Validate and normalize priority level."""
        clean_p = cls.sanitize_string(priority_str, max_length=20, allow_empty=False).capitalize()
        valid_values = [p.value for p in Priority]
        for val in valid_values:
            if clean_p.lower() == val.lower():
                return val
        raise ValidationError(f"Invalid priority '{priority_str}'. Must be one of: {', '.join(valid_values)}")

    @classmethod
    def validate_category(cls, category_str: str) -> str:
        """Validate and normalize category."""
        clean_cat = cls.sanitize_string(category_str, max_length=30, allow_empty=False).capitalize()
        valid_values = [c.value for c in Category]
        for val in valid_values:
            if clean_cat.lower() == val.lower():
                return val
        # Allow custom categories if sanitized
        return clean_cat

    @classmethod
    def validate_status(cls, status_str: str) -> str:
        """Validate reminder status."""
        clean_s = cls.sanitize_string(status_str, max_length=20, allow_empty=False).capitalize()
        valid_values = [s.value for s in ReminderStatus]
        for val in valid_values:
            if clean_s.lower() == val.lower():
                return val
        raise ValidationError(f"Invalid status '{status_str}'. Must be one of: {', '.join(valid_values)}")

    @classmethod
    def prompt_validated_input(cls, prompt_msg: str, validator_func, default: Optional[str] = None) -> str:
        """
        Console input loop wrapper that reprompts on ValidationError until valid value is provided.
        Facilitates resilient terminal UX.
        """
        while True:
            try:
                suffix = f" [{default}]" if default is not None else ""
                raw = input(f"{prompt_msg}{suffix}: ").strip()
                if not raw and default is not None:
                    return default
                return validator_func(raw)
            except ValidationError as ve:
                print(f"  ❌ Invalid Input: {ve}. Please try again.")
            except KeyboardInterrupt:
                print("\n  ⚠️ Action cancelled by user.")
                raise
