import csv
import os


class StatusUpdateWriter:
    def __init__(self, destination_dir):
        self.destination_dir = destination_dir

    def ensure_destination_exists(self):
        if not os.path.exists(self.destination_dir):
            os.makedirs(self.destination_dir)

    def get_base_name(self, file_name):
        return os.path.splitext(file_name)[0]

    def clean_row_for_output(self, row, fieldnames):
        output_row = {}

        for field in fieldnames:
            output_row[field] = row.get(field, "")

        return output_row

    def write_success_file(self, file_name, successful_rows):
        self.ensure_destination_exists()

        base_name = self.get_base_name(file_name)
        success_file_name = f"{base_name}_Success.csv"
        success_file_path = os.path.join(self.destination_dir, success_file_name)

        if not successful_rows:
            return {
                "created": False,
                "file_path": success_file_path,
                "record_count": 0
            }

        fieldnames = ["uuid", "accountStatus", "StatusUpdateResult"]

        cleaned_rows = [
            self.clean_row_for_output(row, fieldnames)
            for row in successful_rows
        ]

        with open(success_file_path, mode="w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)

        return {
            "created": True,
            "file_path": success_file_path,
            "record_count": len(cleaned_rows)
        }

    def write_error_file(self, file_name, failed_rows):
        self.ensure_destination_exists()

        base_name = self.get_base_name(file_name)
        error_file_name = f"{base_name}_Error.csv"
        error_file_path = os.path.join(self.destination_dir, error_file_name)

        if not failed_rows:
            return {
                "created": False,
                "file_path": error_file_path,
                "record_count": 0
            }

        fieldnames = ["uuid", "accountStatus", "ErrorCode", "ErrorDescription"]

        cleaned_rows = [
            self.clean_row_for_output(row, fieldnames)
            for row in failed_rows
        ]

        with open(error_file_path, mode="w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)

        return {
            "created": True,
            "file_path": error_file_path,
            "record_count": len(cleaned_rows)
        }