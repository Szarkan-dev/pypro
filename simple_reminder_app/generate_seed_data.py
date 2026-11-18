"""
Script to generate seed datasets (JSON and CSV) containing 36 realistic reminder entries.
Includes normal, boundary, and edge conditions for hackathon demonstration.
"""

import json
import csv
from pathlib import Path
from datetime import datetime, timedelta

def generate_seed():
    now = datetime.now()
    
    # Helper for relative dates
    def rel_date(days_offset, hour=17, minute=0):
        dt = now + timedelta(days=days_offset)
        return dt.strftime(f"%Y-%m-%d {hour:02d}:{minute:02d}")

    seed_items = [
        # --- Overdue Items (Past Dates) ---
        {"id": 1, "title": "Submit Q3 Financial Expense Audit", "category": "Finance", "due_date": rel_date(-10), "priority": "Critical", "description": "Gather all receipts and submit to corporate portal.", "status": "Pending"},
        {"id": 2, "title": "Renew Vehicle Insurance Policy", "category": "Personal", "due_date": rel_date(-5), "priority": "High", "description": "Compare quotes from Geico and State Farm.", "status": "Pending"},
        {"id": 3, "title": "Return Library Reference Books", "category": "Academic", "due_date": rel_date(-2), "priority": "Medium", "description": "Algorithms and Data Structures 4th Edition.", "status": "Pending"},
        {"id": 4, "title": "Pay Monthly Electricity Utility Bill", "category": "Finance", "due_date": rel_date(-1), "priority": "High", "description": "Pay via online portal to avoid late payment fee.", "status": "Pending"},

        # --- Upcoming Items (Next 7 Days) ---
        {"id": 5, "title": "FutureReady Hackathon Prototype Submission", "category": "Academic", "due_date": rel_date(1, 23, 59), "priority": "Critical", "description": "Final commit and video walkthrough recording.", "status": "Pending"},
        {"id": 6, "title": "Weekly Engineering Team Standup", "category": "Work", "due_date": rel_date(2, 9, 30), "priority": "Medium", "description": "Present sprint retrospective slides.", "status": "Pending"},
        {"id": 7, "title": "Annual Dental Hygiene Checkup", "category": "Health", "due_date": rel_date(3, 14, 0), "priority": "Low", "description": "Dr. Smith's clinic at Downtown Medical Center.", "status": "Pending"},
        {"id": 8, "title": "Draft Architecture Proposal v2", "category": "Work", "due_date": rel_date(4, 18, 0), "priority": "High", "description": "Incorporate feedback from Attempt 2 evaluation report.", "status": "Pending"},
        {"id": 9, "title": "Grocery Shopping: Weekly Meal Prep", "category": "Personal", "due_date": rel_date(5, 11, 0), "priority": "Low", "description": "Buy fresh produce, chicken breast, and oats.", "status": "Pending"},
        {"id": 10, "title": "Review CS50 Python Data Persistence Assignment", "category": "Academic", "due_date": rel_date(6, 20, 0), "priority": "High", "description": "Grade peer review submissions on Canvas.", "status": "Pending"},
        {"id": 11, "title": "Quarterly Server Security Patching", "category": "Work", "due_date": rel_date(7, 2, 0), "priority": "Critical", "description": "Apply Kernel security patches to production nodes.", "status": "Pending"},

        # --- Future Items (> 7 Days) ---
        {"id": 12, "title": "Prepare Annual Tax Return Filing", "category": "Finance", "due_date": rel_date(14), "priority": "High", "description": "Organize W2 and 1099 tax forms.", "status": "Pending"},
        {"id": 13, "title": "Renew AWS Solutions Architect Certification", "category": "Work", "due_date": rel_date(20), "priority": "Medium", "description": "Complete practice exam questions on Pearson VUE.", "status": "Pending"},
        {"id": 14, "title": "Plan Family Summer Vacation Itinerary", "category": "Personal", "due_date": rel_date(25), "priority": "Low", "description": "Book hotel rooms and flight tickets.", "status": "Pending"},
        {"id": 15, "title": "Submit Research Paper on ML Optimization", "category": "Academic", "due_date": rel_date(30), "priority": "High", "description": "Camera-ready submission for IEEE Conference.", "status": "Pending"},
        {"id": 16, "title": "Schedule Annual Comprehensive Health Screening", "category": "Health", "due_date": rel_date(35), "priority": "Medium", "description": "Blood test and cardiology consultation.", "status": "Pending"},
        {"id": 17, "title": "Automobile Scheduled Maintenance & Oil Change", "category": "Personal", "due_date": rel_date(40), "priority": "Medium", "description": "50,000 mile comprehensive service.", "status": "Pending"},
        {"id": 18, "title": "Renew Home Broadband Internet Subscription", "category": "Finance", "due_date": rel_date(45), "priority": "Low", "description": "Negotiate promotional rate with ISP.", "status": "Pending"},

        # --- Completed Items ---
        {"id": 19, "title": "Setup Python Virtual Environment & Git Repo", "category": "Work", "due_date": rel_date(-15), "priority": "High", "description": "Initial setup for reminder project.", "status": "Completed", "completed_at": rel_date(-15)},
        {"id": 20, "title": "Read ShelfTalk Attempt 1 Evaluation Feedback", "category": "Academic", "due_date": rel_date(-12), "priority": "Critical", "description": "Analyzed points lost due to missing unit tests.", "status": "Completed", "completed_at": rel_date(-12)},
        {"id": 21, "title": "Analyze ShelfTalk Attempt 2 Grade A Rubric", "category": "Academic", "due_date": rel_date(-8), "priority": "High", "description": "Identified DAO pattern and security validation strengths.", "status": "Completed", "completed_at": rel_date(-8)},
        {"id": 22, "title": "Configure Project Directory Layout & Pytest", "category": "Work", "due_date": rel_date(-4), "priority": "Medium", "description": "Established standard layout matching requirements.", "status": "Completed", "completed_at": rel_date(-4)},
        {"id": 23, "title": "Purchase Hackathon Snacks & Energy Drinks", "category": "Personal", "due_date": rel_date(-3), "priority": "Low", "description": "Stock up for coding marathon.", "status": "Completed", "completed_at": rel_date(-3)},

        # --- Boundary & Edge Cases ---
        {"id": 24, "title": "Boundary: Leap Year Deadline Check", "category": "Academic", "due_date": "2028-02-29 23:59", "priority": "Low", "description": "Testing date handling on leap year boundaries.", "status": "Pending"},
        {"id": 25, "title": "Boundary: End of Century Boundary Test", "category": "Other", "due_date": "2099-12-31 23:59", "priority": "Low", "description": "Maximum allowable year validation boundary test.", "status": "Pending"},
        {"id": 26, "title": "Edge Case: Short Title X", "category": "Other", "due_date": rel_date(12), "priority": "Medium", "description": "Testing minimum string length handling.", "status": "Pending"},
        {"id": 27, "title": "Edge Case: Special Characters & Emojis 🚀🎉!", "category": "Personal", "due_date": rel_date(15), "priority": "High", "description": "Testing UTF-8 encoding in JSON/CSV persistence layer.", "status": "Pending"},
        {"id": 28, "title": "Edge Case: Extremely Long Description Text Boundary", "category": "Work", "due_date": rel_date(18), "priority": "Low", "description": "This is a very detailed description designed to test string truncation and wrap logic in CLI table formatting modules under high line length conditions.", "status": "Pending"},
        {"id": 29, "title": "Edge Case: Minimum Priority Low Item", "category": "Other", "due_date": rel_date(22), "priority": "Low", "description": "Verifying heuristic urgency score calculations for lowest priority.", "status": "Pending"},
        {"id": 30, "title": "Edge Case: High Frequency Alarm Notification", "category": "Health", "due_date": rel_date(1, 8, 0), "priority": "Critical", "description": "Testing early morning alarm calculation.", "status": "Pending"},
        {"id": 31, "title": "Refactor Codebase to Modular DAO Structure", "category": "Work", "due_date": rel_date(2, 17, 0), "priority": "Critical", "description": "Separating database logic from CLI user interface.", "status": "Pending"},
        {"id": 32, "title": "Write Comprehensive Automated Unit Tests", "category": "Academic", "due_date": rel_date(2, 21, 0), "priority": "Critical", "description": "Ensuring 100% test pass rate for evaluation attempt 1.", "status": "Pending"},
        {"id": 33, "title": "Generate Markdown Executive Audit Summary", "category": "Finance", "due_date": rel_date(3, 12, 0), "priority": "High", "description": "Verifying multi-format report exporter.", "status": "Pending"},
        {"id": 34, "title": "Backup Storage Schema Verification", "category": "Work", "due_date": rel_date(4, 15, 0), "priority": "Medium", "description": "Test atomic file writing and backup fallback.", "status": "Pending"},
        {"id": 35, "title": "Final Code Inspection & Clean Packaging", "category": "Academic", "due_date": rel_date(5, 18, 0), "priority": "Critical", "description": "Verify unminified code structure and zero external dependencies.", "status": "Pending"},
        {"id": 36, "title": "Hackathon Demo Walkthrough Practice", "category": "Personal", "due_date": rel_date(6, 19, 0), "priority": "High", "description": "Simulate error recovery, filtering, and restart persistence.", "status": "Pending"}
    ]

    # Write JSON seed
    json_path = Path("/workspace/scratch/simple_reminder_app/data/sample_reminders.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "reminders": seed_items,
        "last_id": 36,
        "updated_at": datetime.now().isoformat()
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Copy to default data file
    default_json = Path("/workspace/scratch/simple_reminder_app/data/reminders.json")
    with open(default_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Write CSV seed
    csv_path = Path("/workspace/scratch/simple_reminder_app/data/sample_reminders.csv")
    headers = ["id", "title", "category", "due_date", "priority", "description", "status", "created_at", "completed_at"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for item in seed_items:
            row = dict(item)
            if "created_at" not in row:
                row["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if "completed_at" not in row or row["completed_at"] is None:
                row["completed_at"] = ""
            writer.writerow(row)

    print(f"✅ Generated {len(seed_items)} seed records in JSON and CSV formats.")

if __name__ == "__main__":
    generate_seed()
