import csv
import os


class StatusUpdateLoader:
    REQUIRED_HEADERS = ["uuid", "accountStatus"]

    def __init__(self, file_path):
        self.file_path = file_path

    def detect_delimiter(self, sample_text):
        try:
            dialect = csv.Sniffer().sniff(sample_text, delimiters=[",", ";", "\t", "|"])
            return dialect.delimiter
        except csv.Error:
            return ","

    def load_rows_to_memory(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Status update file not found: {self.file_path}")

        rows = []

        with open(self.file_path, mode="r", newline="", encoding="utf-8-sig") as file:
            sample_text = file.read(4096)
            file.seek(0)

            delimiter = self.detect_delimiter(sample_text)

            reader = csv.DictReader(file, delimiter=delimiter)

            if reader.fieldnames is None:
                raise ValueError(f"Status update file is empty or missing headers: {self.file_path}")

            headers = [header.strip() for header in reader.fieldnames]

            for row_number, row in enumerate(reader, start=2):
                cleaned_row = {}

                for header in headers:
                    value = row.get(header, "")

                    if value is None:
                        value = ""

                    cleaned_row[header] = value.strip()

                has_any_value = any(
                    str(value).strip()
                    for value in cleaned_row.values()
                )

                if not has_any_value:
                    continue

                cleaned_row["_row_number"] = row_number
                rows.append(cleaned_row)

        return {
            "headers": headers,
            "rows": rows,
            "total_rows": len(rows),
            "delimiter": delimiter
        }