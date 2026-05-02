import csv
import os


class CSVLoader:
    def __init__(self, file_path):
        self.file_path = file_path

    def detect_delimiter(self, sample_text):
        try:
            dialect = csv.Sniffer().sniff(sample_text, delimiters=[",", ";", "\t", "|"])
            return dialect.delimiter
        except csv.Error:
            return ","

    def load_users_to_memory(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

        users = []

        with open(self.file_path, mode="r", newline="", encoding="utf-8-sig") as file:
            sample_text = file.read(4096)
            file.seek(0)

            delimiter = self.detect_delimiter(sample_text)

            reader = csv.DictReader(file, delimiter=delimiter)

            if reader.fieldnames is None:
                raise ValueError(f"CSV file is empty or missing headers: {self.file_path}")

            original_headers = reader.fieldnames
            cleaned_headers = [header.strip() for header in original_headers]

            for row_number, row in enumerate(reader, start=2):
                cleaned_row = {}

                for original_header, cleaned_header in zip(original_headers, cleaned_headers):
                    value = row.get(original_header, "")

                    if value is None:
                        value = ""

                    cleaned_row[cleaned_header] = value.strip()

                cleaned_row["_row_number"] = row_number
                users.append(cleaned_row)

        return {
            "headers": cleaned_headers,
            "users": users,
            "total_users": len(users),
            "delimiter": delimiter
        }