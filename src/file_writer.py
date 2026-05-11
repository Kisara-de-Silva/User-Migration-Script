import csv
import os


class FileWriter:
    def __init__(self, destination_dir, output_fields):
        self.destination_dir = destination_dir
        self.output_fields = output_fields

    def ensure_destination_exists(self):
        if not os.path.exists(self.destination_dir):
            os.makedirs(self.destination_dir)

    def get_batch_base_name(self, batch_file_name):
        return os.path.splitext(batch_file_name)[0]

    def remove_internal_fields(self, user):
        cleaned_user = {}

        for key, value in user.items():
            if not key.startswith("_"):
                cleaned_user[key] = value

        return cleaned_user

    def write_success_file(self, batch_file_name, successful_users):
        self.ensure_destination_exists()

        batch_base_name = self.get_batch_base_name(batch_file_name)
        success_file_name = f"{batch_base_name}_Success.csv"
        success_file_path = os.path.join(self.destination_dir, success_file_name)

        if not successful_users:
            return {
                "created": False,
                "file_path": success_file_path,
                "record_count": 0
            }

        output_headers = list(self.output_fields)

        cleaned_users = []

        for user in successful_users:
            cleaned_user = self.remove_internal_fields(user)

            output_row = {}
            for header in output_headers:
                output_row[header] = cleaned_user.get(header, "")

            cleaned_users.append(output_row)

        with open(success_file_path, mode="w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=output_headers)
            writer.writeheader()
            writer.writerows(cleaned_users)

        return {
            "created": True,
            "file_path": success_file_path,
            "record_count": len(cleaned_users)
        }

    def write_error_file(self, batch_file_name, failed_users):
        self.ensure_destination_exists()

        batch_base_name = self.get_batch_base_name(batch_file_name)
        error_file_name = f"{batch_base_name}_Error.csv"
        error_file_path = os.path.join(self.destination_dir, error_file_name)

        if not failed_users:
            return {
                "created": False,
                "file_path": error_file_path,
                "record_count": 0
            }

        output_headers = list(self.output_fields)

        if "ErrorCode" not in output_headers:
            output_headers.append("ErrorCode")

        if "ErrorDescription" not in output_headers:
            output_headers.append("ErrorDescription")

        cleaned_users = []

        for user in failed_users:
            cleaned_user = self.remove_internal_fields(user)

            output_row = {}
            for header in output_headers:
                output_row[header] = cleaned_user.get(header, "")

            cleaned_users.append(output_row)

        with open(error_file_path, mode="w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=output_headers)
            writer.writeheader()
            writer.writerows(cleaned_users)

        return {
            "created": True,
            "file_path": error_file_path,
            "record_count": len(cleaned_users)
        }