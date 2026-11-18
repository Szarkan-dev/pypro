"""
Interactive Console UI & Terminal Navigation Dispatcher.

Provides ANSI-formatted terminal prompts, interactive menu handlers, pagination wrappers,
and executive report visualization routines for the Simple Reminder List application.
"""

import os
import sys
from datetime import datetime
from typing import Optional, List

from src.models import Reminder, Priority, Category, ReminderStatus
from src.storage import ReminderDAO, StorageError
from src.validation import InputValidator, ValidationError
from src.analytics import ReminderAnalytics


class ConsoleUI:
    """Terminal user interface manager and main event dispatch loop."""

    # ANSI Color Code Constants
    HEADER = "\033[95m\033[1m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m\033[1m"
    YELLOW = "\033[93m"
    RED = "\033[91m\033[1m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, data_file: str = "data/reminders.json"):
        self.dao = ReminderDAO(data_file)
        self.page_size = 10

    def clear_screen(self):
        """Clear the console terminal buffer cleanly."""
        os.system("cls" if os.name == "nt" else "clear")

    def print_banner(self):
        """Render branded terminal banner."""
        print(f"{self.CYAN}======================================================================={self.RESET}")
        print(f"{self.HEADER}         ⏰ SIMPLE REMINDER LIST — FUTURE READY HACK v1.0{self.RESET}")
        print(f"{self.CYAN}   Zero-Dependency Python Productivity Engine | Terminal Console UI{self.RESET}")
        print(f"{self.CYAN}======================================================================={self.RESET}")

    def display_main_menu(self):
        """Render interactive main menu options."""
        print(f"\n{self.BOLD}📋 MAIN MENU OPTIONS:{self.RESET}")
        print(f"  {self.GREEN}[1]{self.RESET} View All Reminders (Paginated Table)")
        print(f"  {self.GREEN}[2]{self.RESET} 📅 View Upcoming Reminders (Next 7 Days)")
        print(f"  {self.RED}[3]{self.RESET} 🚨 View Overdue Items & High-Urgency Tasks")
        print(f"  {self.GREEN}[4]{self.RESET} ➕ Add New Reminder (Defensive Input)")
        print(f"  {self.GREEN}[5]{self.RESET} 🔍 Search & Filter Reminders")
        print(f"  {self.GREEN}[6]{self.RESET} ✏️  Update / Mark Complete / Delete Reminder")
        print(f"  {self.GREEN}[7]{self.RESET} 📊 Executive Analytics Summary")
        print(f"  {self.GREEN}[8]{self.RESET} 📄 Export Markdown Audit Report / Backup")
        print(f"  {self.YELLOW}[9]{self.RESET} 🧪 Run Diagnostic Test Suite (Self-Check)")
        print(f"  {self.BLUE}[0]{self.RESET} 🚪 Exit Program")

    def run(self):
        """Main interaction dispatch loop."""
        self.clear_screen()
        self.print_banner()

        # Display threshold warning banner if overdue items exist
        self._check_and_print_overdue_warning()

        while True:
            self.display_main_menu()
            choice = input(f"\n{self.BOLD}Select menu option [0-9]: {self.RESET}").strip()

            if choice == "1":
                self.handle_view_all()
            elif choice == "2":
                self.handle_view_upcoming()
            elif choice == "3":
                self.handle_view_overdue()
            elif choice == "4":
                self.handle_add_reminder()
            elif choice == "5":
                self.handle_search_filter()
            elif choice == "6":
                self.handle_update_delete()
            elif choice == "7":
                self.handle_executive_summary()
            elif choice == "8":
                self.handle_export_reports()
            elif choice == "9":
                self.handle_run_diagnostics()
            elif choice == "0":
                print(f"\n{self.GREEN}Thank you for using Simple Reminder List! Goodbye.{self.RESET}\n")
                sys.exit(0)
            else:
                print(f"  ❌ Invalid selection '{choice}'. Please enter a number between 0 and 9.")

    def _check_and_print_overdue_warning(self):
        """Print prominent threshold warning banner if overdue pending items exist."""
        try:
            reminders = self.dao.load_all()
            overdue = ReminderAnalytics.get_overdue_reminders(reminders)
            if overdue:
                print(f"\n{self.RED}🚨 WARNING: You have {len(overdue)} OVERDUE pending reminder(s)! Select option [3] to inspect.{self.RESET}")
        except StorageError as se:
            print(f"\n{self.YELLOW}⚠️ Storage Warning: {se}{self.RESET}")

    def handle_view_all(self):
        """Render all reminders with page navigation."""
        reminders = self.dao.load_all()
        if not reminders:
            print(f"\n{self.YELLOW}No reminders in database. Select option [4] to create one.{self.RESET}")
            return

        current_page = 1
        while True:
            self.clear_screen()
            self.print_banner()
            print(f"\n{self.BOLD}📋 ALL REMINDERS DATASET:{self.RESET}\n")
            table_str, total_pages = ReminderAnalytics.format_terminal_table(
                reminders, page=current_page, page_size=self.page_size
            )
            print(table_str)

            print(f"\nNavigation: [{self.GREEN}N{self.RESET}]ext Page | [{self.GREEN}P{self.RESET}]rev Page | [{self.GREEN}B{self.RESET}]ack to Menu")
            nav = input("Choice [N/P/B]: ").strip().upper()
            if nav == "N" and current_page < total_pages:
                current_page += 1
            elif nav == "P" and current_page > 1:
                current_page -= 1
            elif nav == "B":
                break

    def handle_view_upcoming(self):
        """Display pending reminders due within next 7 days."""
        reminders = self.dao.load_all()
        upcoming = ReminderAnalytics.get_upcoming_reminders(reminders, days=7)
        self.clear_screen()
        self.print_banner()
        print(f"\n{self.BOLD}📅 UPCOMING REMINDERS (NEXT 7 DAYS):{self.RESET}\n")
        table_str, _ = ReminderAnalytics.format_terminal_table(upcoming, page=1, page_size=20)
        print(table_str)
        input(f"\nPress Enter to return to main menu...")

    def handle_view_overdue(self):
        """Display overdue items ranked by urgency score."""
        reminders = self.dao.load_all()
        overdue = ReminderAnalytics.get_overdue_reminders(reminders)
        self.clear_screen()
        self.print_banner()
        print(f"\n{self.RED}🚨 OVERDUE & CRITICAL ITEMS:{self.RESET}\n")
        if not overdue:
            print(f"  {self.GREEN}🎉 Great job! You have zero overdue items.{self.RESET}")
        else:
            table_str, _ = ReminderAnalytics.format_terminal_table(overdue, page=1, page_size=20)
            print(table_str)
        input(f"\nPress Enter to return to main menu...")

    def handle_add_reminder(self):
        """Interactively prompt user to add a new reminder with defensive error recovery."""
        self.clear_screen()
        self.print_banner()
        print(f"\n{self.BOLD}➕ ADD NEW REMINDER (Defensive Input Mode):{self.RESET}")
        print("  (Intentionally enter bad dates or blank text to test resilience)\n")

        try:
            title = InputValidator.prompt_validated_input(
                "1. Enter Reminder Title (2-100 chars)",
                InputValidator.validate_title
            )

            print(f"   Categories: {', '.join([c.value for c in Category])}")
            category = InputValidator.prompt_validated_input(
                "2. Enter Category",
                InputValidator.validate_category,
                default=Category.WORK.value
            )

            due_date = InputValidator.prompt_validated_input(
                "3. Enter Due Date (Format: YYYY-MM-DD or YYYY-MM-DD HH:MM)",
                InputValidator.validate_date
            )

            print(f"   Priorities: {', '.join([p.value for p in Priority])}")
            priority = InputValidator.prompt_validated_input(
                "4. Enter Priority",
                InputValidator.validate_priority,
                default=Priority.MEDIUM.value
            )

            desc = input("5. Enter Description (Optional, press Enter to skip): ").strip()

            new_reminder = Reminder(
                id=0,
                title=title,
                category=category,
                due_date=due_date,
                priority=priority,
                description=desc,
                status=ReminderStatus.PENDING.value
            )

            saved = self.dao.add(new_reminder)
            print(f"\n{self.GREEN}✅ SUCCESS: Saved Reminder #{saved.id} '{saved.title}' to persistent storage!{self.RESET}")

        except KeyboardInterrupt:
            print(f"\n{self.YELLOW}Action cancelled.{self.RESET}")

        input(f"\nPress Enter to return to main menu...")

    def handle_search_filter(self):
        """Prompt search criteria and display filtered subset."""
        self.clear_screen()
        self.print_banner()
        print(f"\n{self.BOLD}🔍 SEARCH & FILTER REMINDERS:{self.RESET}")

        kw = input("Enter search keyword (or press Enter to skip): ").strip()
        cat = input("Filter by Category (e.g. Work, Finance, Academic, or Enter to skip): ").strip()
        prio = input("Filter by Priority (e.g. High, Critical, Low, or Enter to skip): ").strip()
        st = input("Filter by Status (e.g. Pending, Completed, or Enter to skip): ").strip()

        reminders = self.dao.load_all()
        filtered = ReminderAnalytics.filter_reminders(
            reminders,
            keyword=kw if kw else None,
            category=cat if cat else None,
            priority=prio if prio else None,
            status=st if st else None
        )

        print(f"\n{self.BOLD}Results ({len(filtered)} items matched):{self.RESET}\n")
        table_str, _ = ReminderAnalytics.format_terminal_table(filtered, page=1, page_size=20)
        print(table_str)
        input(f"\nPress Enter to return to main menu...")

    def handle_update_delete(self):
        """Prompt ID to edit status, update details, or delete."""
        self.clear_screen()
        self.print_banner()
        print(f"\n{self.BOLD}✏️ UPDATE / DELETE REMINDER:{self.RESET}\n")

        try:
            id_str = input("Enter Reminder ID to modify: ").strip()
            if not id_str.isdigit():
                print(f"  ❌ Invalid ID format. Must be an integer.")
                input("\nPress Enter to return...")
                return

            r_id = int(id_str)
            reminder = self.dao.get_by_id(r_id)
            if not reminder:
                print(f"  ❌ Reminder #{r_id} not found in database.")
                input("\nPress Enter to return...")
                return

            print(f"\nFound Reminder #{reminder.id}: {self.BOLD}{reminder.title}{self.RESET}")
            print(f"  Status: {reminder.status} | Priority: {reminder.priority} | Due: {reminder.due_date}")
            print("\nOptions:")
            print("  [1] Mark as Completed")
            print("  [2] Change Priority")
            print("  [3] Edit Due Date")
            print("  [4] Delete Reminder")
            print("  [0] Cancel")

            act = input("Select Action [0-4]: ").strip()
            if act == "1":
                reminder.status = ReminderStatus.COMPLETED.value
                reminder.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.dao.update(reminder)
                print(f"\n{self.GREEN}✅ Reminder #{reminder.id} marked as Completed!{self.RESET}")
            elif act == "2":
                prio = InputValidator.prompt_validated_input("Enter New Priority", InputValidator.validate_priority)
                reminder.priority = prio
                self.dao.update(reminder)
                print(f"\n{self.GREEN}✅ Priority updated to {prio}!{self.RESET}")
            elif act == "3":
                d_date = InputValidator.prompt_validated_input("Enter New Due Date", InputValidator.validate_date)
                reminder.due_date = d_date
                self.dao.update(reminder)
                print(f"\n{self.GREEN}✅ Due date updated to {d_date}!{self.RESET}")
            elif act == "4":
                confirm = input(f"Are you sure you want to DELETE #{reminder.id}? (y/N): ").strip().lower()
                if confirm == "y":
                    self.dao.delete(reminder.id)
                    print(f"\n{self.GREEN}✅ Reminder #{reminder.id} deleted successfully.{self.RESET}")
                else:
                    print("\nDeletion cancelled.")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        input(f"\nPress Enter to return to main menu...")

    def handle_executive_summary(self):
        """Compute and display formatted executive metrics table."""
        self.clear_screen()
        self.print_banner()
        reminders = self.dao.load_all()
        metrics = ReminderAnalytics.generate_summary_metrics(reminders)

        print(f"\n{self.HEADER}📊 EXECUTIVE ANALYTICS SUMMARY DASHBOARD{self.RESET}")
        print(f"Generated at: {metrics['generated_at']}\n")
        print(f"  ┌─────────────────────────────────┬────────────────────┐")
        print(f"  │ KPI Metric Description          │ Value / Breakdown  │")
        print(f"  ├─────────────────────────────────┼────────────────────┤")
        print(f"  │ Total Active Records            │ {str(metrics['total_records']).ljust(18)} │")
        print(f"  │ Pending Reminders               │ {str(metrics['pending_count']).ljust(18)} │")
        print(f"  │ Completed Reminders             │ {str(metrics['completed_count']).ljust(18)} │")
        print(f"  │ Overdue Reminders (Alert)       │ {str(metrics['overdue_count']).ljust(18)} │")
        print(f"  │ Upcoming Reminders (7 Days)     │ {str(metrics['upcoming_7d_count']).ljust(18)} │")
        print(f"  │ Completion Rate Percentage      │ {(str(metrics['completion_rate_pct']) + '%').ljust(18)} │")
        print(f"  │ Overdue Rate (of Pending)       │ {(str(metrics['overdue_rate_pct']) + '%').ljust(18)} │")
        print(f"  └─────────────────────────────────┴────────────────────┘")

        print(f"\n{self.BOLD}Category Breakdown:{self.RESET}")
        for cat, count in metrics["category_breakdown"].items():
            bar = "█" * min(20, count)
            print(f"  {cat.ljust(12)} : {str(count).rjust(2)} {self.CYAN}{bar}{self.RESET}")

        input(f"\nPress Enter to return to main menu...")

    def handle_export_reports(self):
        """Export Markdown report and timestamped database backups."""
        self.clear_screen()
        self.print_banner()
        print(f"\n{self.BOLD}📄 EXPORT REPORTS & DATA BACKUP:{self.RESET}\n")

        reminders = self.dao.load_all()
        md_file = ReminderAnalytics.export_markdown_report(reminders, "exports/reminder_executive_summary.md")
        backup_file = self.dao.create_backup("data/backups")

        print(f"{self.GREEN}✅ Markdown Report Exported:{self.RESET} {md_file.resolve()}")
        print(f"{self.GREEN}✅ Database Backup Saved:{self.RESET}    {backup_file.resolve()}")

        input(f"\nPress Enter to return to main menu...")

    def handle_run_diagnostics(self):
        """Execute automated unittest suite directly from CLI."""
        self.clear_screen()
        self.print_banner()
        print(f"\n{self.YELLOW}🧪 RUNNING AUTOMATED SYSTEM DIAGNOSTICS...{self.RESET}\n")

        import unittest
        loader = unittest.TestLoader()
        tests_dir = os.path.join(os.path.dirname(__file__), "..", "tests")
        suite = loader.discover(start_dir=tests_dir, pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        if result.wasSuccessful():
            print(f"\n{self.GREEN}🎉 ALL SYSTEM DIAGNOSTIC TESTS PASSED (100% PASS RATE).{self.RESET}")
        else:
            print(f"\n{self.RED}❌ DIAGNOSTIC FAILURES DETECTED.{self.RESET}")

        input(f"\nPress Enter to return to main menu...")
