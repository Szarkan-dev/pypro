"""
Analytics, Reporting, and Query Engine for Simple Reminder List Application.

Computes executive summaries, calculates completion rates, aggregates status indicators,
ranks urgency using custom heuristics, and generates formatted Markdown/CSV audit reports.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.models import Reminder, ReminderStatus, Priority, Category


class ReminderAnalytics:
    """Analytics and report generation engine for reminder datasets."""

    @staticmethod
    def generate_summary_metrics(reminders: List[Reminder], reference_dt: Optional[datetime] = None) -> Dict[str, Any]:
        """Compute aggregated statistics, counts, percentages, and breakdowns."""
        ref = reference_dt or datetime.now()
        total = len(reminders)
        if total == 0:
            return {
                "total_records": 0,
                "pending_count": 0,
                "completed_count": 0,
                "archived_count": 0,
                "overdue_count": 0,
                "upcoming_7d_count": 0,
                "completion_rate_pct": 0.0,
                "overdue_rate_pct": 0.0,
                "category_breakdown": {},
                "priority_breakdown": {},
                "generated_at": ref.strftime("%Y-%m-%d %H:%M:%S")
            }

        pending = [r for r in reminders if r.status == ReminderStatus.PENDING.value]
        completed = [r for r in reminders if r.status == ReminderStatus.COMPLETED.value]
        archived = [r for r in reminders if r.status == ReminderStatus.ARCHIVED.value]

        overdue = [r for r in pending if r.is_overdue(ref)]
        upcoming = [r for r in pending if r.is_upcoming(days=7, reference_dt=ref)]

        completion_rate = round((len(completed) / total) * 100.0, 1)
        overdue_rate = round((len(overdue) / len(pending)) * 100.0, 1) if pending else 0.0

        # Category Breakdown
        cat_counts: Dict[str, int] = {}
        for r in reminders:
            cat_counts[r.category] = cat_counts.get(r.category, 0) + 1

        # Priority Breakdown (Pending items)
        prio_counts: Dict[str, int] = {}
        for r in pending:
            prio_counts[r.priority] = prio_counts.get(r.priority, 0) + 1

        return {
            "total_records": total,
            "pending_count": len(pending),
            "completed_count": len(completed),
            "archived_count": len(archived),
            "overdue_count": len(overdue),
            "upcoming_7d_count": len(upcoming),
            "completion_rate_pct": completion_rate,
            "overdue_rate_pct": overdue_rate,
            "category_breakdown": cat_counts,
            "priority_breakdown": prio_counts,
            "generated_at": ref.strftime("%Y-%m-%d %H:%M:%S")
        }

    @staticmethod
    def get_overdue_reminders(reminders: List[Reminder], reference_dt: Optional[datetime] = None) -> List[Reminder]:
        """Extract and sort overdue pending reminders by overdue duration descending."""
        ref = reference_dt or datetime.now()
        overdue = [r for r in reminders if r.is_overdue(ref)]
        return sorted(overdue, key=lambda r: r.parse_due_date())

    @staticmethod
    def get_upcoming_reminders(reminders: List[Reminder], days: int = 7, reference_dt: Optional[datetime] = None) -> List[Reminder]:
        """Extract and sort pending reminders due within next N days."""
        ref = reference_dt or datetime.now()
        upcoming = [r for r in reminders if r.is_upcoming(days=days, reference_dt=ref)]
        return sorted(upcoming, key=lambda r: r.parse_due_date())

    @staticmethod
    def rank_by_urgency(reminders: List[Reminder], reference_dt: Optional[datetime] = None) -> List[Reminder]:
        """Rank pending reminders using urgency heuristic score."""
        ref = reference_dt or datetime.now()
        pending = [r for r in reminders if r.status == ReminderStatus.PENDING.value]
        return sorted(pending, key=lambda r: r.urgency_score(ref), reverse=True)

    @staticmethod
    def filter_reminders(
        reminders: List[Reminder],
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Reminder]:
        """Filter reminders by multiple criteria."""
        result = reminders
        if keyword:
            kw = keyword.lower().strip()
            result = [
                r for r in result
                if kw in r.title.lower() or kw in r.description.lower() or kw in str(r.id)
            ]
        if category:
            cat = category.lower().strip()
            result = [r for r in result if r.category.lower() == cat]
        if priority:
            prio = priority.lower().strip()
            result = [r for r in result if r.priority.lower() == prio]
        if status:
            st = status.lower().strip()
            result = [r for r in result if r.status.lower() == st]

        return result

    @classmethod
    def export_markdown_report(
        cls,
        reminders: List[Reminder],
        output_file: str = "exports/reminder_executive_summary.md",
        reference_dt: Optional[datetime] = None
    ) -> Path:
        """Generate a publication-ready Markdown executive report."""
        ref = reference_dt or datetime.now()
        metrics = cls.generate_summary_metrics(reminders, ref)
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        overdue_items = cls.get_overdue_reminders(reminders, ref)
        upcoming_items = cls.get_upcoming_reminders(reminders, 7, ref)

        md_content = []
        md_content.append("# 📋 Simple Reminder List — Executive Audit Report")
        md_content.append(f"**Generated On:** {metrics['generated_at']} | **Total Records:** {metrics['total_records']}\n")

        md_content.append("## 📊 KPI Metrics Summary")
        md_content.append("| Metric | Count / Value | Ratio (%) | Status Indicator |")
        md_content.append("| :--- | :---: | :---: | :---: |")
        md_content.append(f"| **Total Reminders** | {metrics['total_records']} | 100.0% | ℹ️ Total Active Dataset |")
        md_content.append(f"| **Pending Tasks** | {metrics['pending_count']} | {round((metrics['pending_count']/metrics['total_records'])*100, 1) if metrics['total_records'] else 0}% | ⏳ Action Required |")
        md_content.append(f"| **Completed Tasks** | {metrics['completed_count']} | {metrics['completion_rate_pct']}% | ✅ Achieved |")
        md_content.append(f"| **Overdue Items** | {metrics['overdue_count']} | {metrics['overdue_rate_pct']}% (of pending) | 🚨 **ATTENTION REQUIRED** |")
        md_content.append(f"| **Upcoming (7 Days)** | {metrics['upcoming_7d_count']} | — | 📅 High Priority Watchlist |\n")

        md_content.append("## 🏷️ Category Breakdown")
        md_content.append("| Category | Total Reminders | Share (%) |")
        md_content.append("| :--- | :---: | :---: |")
        for cat, cnt in metrics["category_breakdown"].items():
            pct = round((cnt / metrics['total_records']) * 100, 1) if metrics['total_records'] else 0
            md_content.append(f"| {cat} | {cnt} | {pct}% |")
        md_content.append("")

        if overdue_items:
            md_content.append("## 🚨 Overdue Items (Immediate Action)")
            md_content.append("| ID | Title | Category | Priority | Due Date | Days Overdue |")
            md_content.append("| :-: | :--- | :--- | :--- | :--- | :-: |")
            for item in overdue_items:
                days_over = abs(item.days_remaining(ref))
                md_content.append(f"| #{item.id} | {item.title} | {item.category} | **{item.priority}** | `{item.due_date}` | **{days_over} days** |")
            md_content.append("")

        if upcoming_items:
            md_content.append("## 📅 Upcoming Items (Next 7 Days)")
            md_content.append("| ID | Title | Category | Priority | Due Date | Days Remaining |")
            md_content.append("| :-: | :--- | :--- | :--- | :--- | :-: |")
            for item in upcoming_items:
                days_left = item.days_remaining(ref)
                md_content.append(f"| #{item.id} | {item.title} | {item.category} | {item.priority} | `{item.due_date}` | {days_left} days |")
            md_content.append("")

        md_content.append("---\n*Report generated automatically by Simple Reminder List Analytics Module (Zero External Dependencies).*")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))

        return out_path

    @staticmethod
    def format_terminal_table(
        reminders: List[Reminder],
        page: int = 1,
        page_size: int = 10,
        reference_dt: Optional[datetime] = None
    ) -> Tuple[str, int]:
        """Format a list of reminders into a clean ANSI ASCII table with pagination."""
        ref = reference_dt or datetime.now()
        total_items = len(reminders)
        if total_items == 0:
            return "  (No reminders found matching query criteria)", 1

        total_pages = (total_items + page_size - 1) // page_size
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        page_items = reminders[start_idx: start_idx + page_size]

        # Column widths
        # ID(4), Title(28), Category(12), Due Date(16), Priority(10), Status(10)
        lines = []
        lines.append(f"┌──────┬──────────────────────────────┬──────────────┬──────────────────┬────────────┬───────────┐")
        lines.append(f"│ ID   │ Title                        │ Category     │ Due Date         │ Priority   │ Status    │")
        lines.append(f"├──────┼──────────────────────────────┼──────────────┼──────────────────┼────────────┼───────────┤")

        for r in page_items:
            title_str = (r.title[:25] + "...") if len(r.title) > 28 else r.title.ljust(28)
            cat_str = (r.category[:11] + ".") if len(r.category) > 12 else r.category.ljust(12)
            due_str = r.due_date[:16].ljust(16)
            prio_str = r.priority.ljust(10)

            # Highlight status/overdue
            status_flag = r.status
            if r.is_overdue(ref):
                status_flag = "OVERDUE!"

            stat_str = status_flag.ljust(9)
            id_str = f"#{r.id}".ljust(4)

            lines.append(f"│ {id_str} │ {title_str} │ {cat_str} │ {due_str} │ {prio_str} │ {stat_str} │")

        lines.append(f"└──────┴──────────────────────────────┴──────────────┴──────────────────┴────────────┴───────────┘")
        lines.append(f"  Showing Page {page} of {total_pages} ({total_items} total records)")

        return "\n".join(lines), total_pages
