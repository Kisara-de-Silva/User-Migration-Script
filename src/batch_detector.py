import os
import re


class BatchDetector:
    def __init__(self, source_dir, batch_prefix, batch_extension):
        self.source_dir = source_dir
        self.batch_prefix = batch_prefix
        self.batch_extension = batch_extension

        self.pattern = re.compile(
            rf"^{re.escape(batch_prefix)}(\d+){re.escape(batch_extension)}$"
        )

    def detect_batches(self):
        if not os.path.exists(self.source_dir):
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")

        detected_batches = []

        for file_name in os.listdir(self.source_dir):
            match = self.pattern.match(file_name)

            if match:
                sequence_text = match.group(1)
                sequence_number = int(sequence_text)

                detected_batches.append({
                    "file_name": file_name,
                    "file_path": os.path.join(self.source_dir, file_name),
                    "sequence_text": sequence_text,
                    "sequence_number": sequence_number
                })

        detected_batches.sort(key=lambda batch: batch["sequence_number"])

        return detected_batches