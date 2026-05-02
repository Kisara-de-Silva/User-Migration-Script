from src.config_loader import ConfigLoader
from src.batch_detector import BatchDetector
from src.tracker import MigrationTracker
from src.csv_loader import CSVLoader
from src.validator import UserValidator


def main():
    config_loader = ConfigLoader()
    config_loader.load_config()

    paths = config_loader.get_paths()
    target = config_loader.get_target_config()
    batch_config = config_loader.get_batch_config()
    validation_config = config_loader.get_validation_config()

    print("Configuration loaded successfully.")
    print("Paths:", paths)
    print("Target:", target)
    print("Batch Config:", batch_config)
    print("Validation Config:", validation_config)

    batch_detector = BatchDetector(
        source_dir=paths["source_dir"],
        batch_prefix=batch_config["batch_prefix"],
        batch_extension=batch_config["batch_extension"]
    )

    tracker = MigrationTracker(
        tracker_file=paths["tracker_file"]
    )

    tracker.ensure_tracker_exists()

    batches = batch_detector.detect_batches()

    print("\nDetected Batch Files:")

    if not batches:
        print("No valid batch files found.")
        return

    for batch in batches:
        batch_file_name = batch["file_name"]

        if tracker.is_batch_executed(batch_file_name):
            print(
                f"SKIPPED | File: {batch_file_name} | "
                f"Sequence: {batch['sequence_number']} | "
                f"Reason: Already executed"
            )
            continue

        print(
            f"PENDING | File: {batch_file_name} | "
            f"Sequence: {batch['sequence_number']} | "
            f"Path: {batch['file_path']}"
        )

        print(f"\nLoading CSV data into memory for batch: {batch_file_name}")

        csv_loader = CSVLoader(batch["file_path"])
        csv_data = csv_loader.load_users_to_memory()

        headers = csv_data["headers"]
        users = csv_data["users"]
        total_users = csv_data["total_users"]
        delimiter = csv_data["delimiter"]

        print("CSV loaded successfully into memory.")
        print(f"Detected delimiter: {repr(delimiter)}")
        print(f"Headers found: {len(headers)}")
        print(f"Total users loaded: {total_users}")

        if total_users > 0:
            first_user = users[0]
            print(
                "First user sample: "
                f"Row={first_user.get('_row_number')} | "
                f"LoginID={first_user.get('loginid', 'N/A')} | "
                f"isCorpUser={first_user.get('isCorpUser', 'N/A')} | "
                f"CIF={first_user.get('cifnumber', 'N/A')}"
            )

        print(f"\nValidating users for batch: {batch_file_name}")

        validator = UserValidator(
            mandatory_fields=validation_config["mandatory_fields"],
            true_values=validation_config["true_values"],
            false_values=validation_config["false_values"]
        )

        validation_result = validator.validate_users(users)

        valid_users = validation_result["valid_users"]
        invalid_users = validation_result["invalid_users"]

        print("Validation completed.")
        print(f"Valid users: {validation_result['total_valid']}")
        print(f"Invalid users: {validation_result['total_invalid']}")

        if invalid_users:
            print("\nInvalid User Details:")

            for invalid_user in invalid_users:
                print(
                    f"Row={invalid_user.get('_row_number')} | "
                    f"LoginID={invalid_user.get('loginid', 'N/A')} | "
                    f"ErrorCode={invalid_user.get('ErrorCode')} | "
                    f"ErrorDescription={invalid_user.get('ErrorDescription')}"
                )


if __name__ == "__main__":
    main()