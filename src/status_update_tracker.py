import csv
import os
from datetime import datetime


class StatusUpdateTracker:
    def __init__(self, tracker_file):
        self.tracker_file = tracker_file

        self.fieldnames = [
            "status_update_file_name",
            "sequence_number",
            "executed",
            "total_status_updates_success",
            "total_status_updates_failed",
            "started_at",
            "completed_at"
        ]

    def ensure_tracker_exists(self):
        tracker_dir = os.path.dirname(self.tracker_file)

        if tracker_dir and not os.path.exists(tracker_dir):
            os.makedirs(tracker_dir)

        if not os.path.exists(self.tracker_file):
            with open(self.tracker_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def read_tracker_rows(self):
        self.ensure_tracker_exists()

        with open(self.tracker_file, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader)

    def is_file_executed(self, status_update_file_name):
        rows = self.read_tracker_rows()

        for row in rows:
            if (
                row.get("status_update_file_name") == status_update_file_name
                and row.get("executed", "").strip().lower() == "true"
            ):
                return True

        return False

    def record_status_update_result(
        self,
        status_update_file_name,
        sequence_number,
        total_success,
        total_failed,
        started_at,
        completed_at=None
    ):
        self.ensure_tracker_exists()

        if completed_at is None:
            completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_row = {
            "status_update_file_name": status_update_file_name,
            "sequence_number": sequence_number,
            "executed": "true",
            "total_status_updates_success": total_success,
            "total_status_updates_failed": total_failed,
            "started_at": started_at,
            "completed_at": completed_at
        }

        with open(self.tracker_file, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(new_row)