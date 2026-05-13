from datetime import datetime

from src.config_loader import ConfigLoader
from src.batch_detector import BatchDetector
from src.status_update_tracker import StatusUpdateTracker
from src.status_update_loader import StatusUpdateLoader
from src.status_update_validator import StatusUpdateValidator
from src.status_update_engine import StatusUpdateEngine
from src.status_update_writer import StatusUpdateWriter
from src.scim_client import SCIMClient
from src.logger_setup import setup_batch_logger


def main():
    config_loader = ConfigLoader()
    config_loader.load_config()

    paths = config_loader.get_paths()
    target = config_loader.get_target_config()
    auth_config = config_loader.get_auth_config()
    http_config = config_loader.get_http_config()
    status_update_config = config_loader.get_status_update_config()

    print("Status Update Configuration loaded successfully.")
    print("Paths:", paths)
    print("Target:", target)
    print("Auth Config:", {
        "auth_type": auth_config["auth_type"],
        "username": auth_config["username"],
        "password": "***MASKED***"
    })
    print("HTTP Config:", http_config)
    print("Status Update Config:", status_update_config)

    status_update_detector = BatchDetector(
        source_dir=paths["source_dir"],
        batch_prefix=status_update_config["status_update_prefix"],
        batch_extension=status_update_config["status_update_extension"]
    )

    status_update_tracker = StatusUpdateTracker(
        tracker_file=paths["status_update_tracker_file"]
    )

    status_update_tracker.ensure_tracker_exists()

    files = status_update_detector.detect_batches()

    print("\nDetected Status Update Files:")

    if not files:
        print("No valid status update files found.")
        return

    for file_info in files:
        file_name = file_info["file_name"]

        if status_update_tracker.is_file_executed(file_name):
            print(
                f"SKIPPED | File: {file_name} | "
                f"Sequence: {file_info['sequence_number']} | "
                f"Reason: Already executed"
            )
            continue

        print(
            f"PENDING | File: {file_name} | "
            f"Sequence: {file_info['sequence_number']} | "
            f"Path: {file_info['file_path']}"
        )

        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        batch_logger = setup_batch_logger(
            log_dir=paths["log_dir"],
            batch_file_name=file_name
        )

        batch_logger.info("=" * 80)
        batch_logger.info(f"Status update processing started | File={file_name}")
        batch_logger.info(f"Sequence Number={file_info['sequence_number']}")
        batch_logger.info(f"Source File={file_info['file_path']}")
        batch_logger.info(f"Target URL={target['delete_user_url']}")

        print(f"\nLoading status update file into memory: {file_name}")

        loader = StatusUpdateLoader(file_info["file_path"])
        loaded_data = loader.load_rows_to_memory()

        headers = loaded_data["headers"]
        rows = loaded_data["rows"]
        total_rows = loaded_data["total_rows"]
        delimiter = loaded_data["delimiter"]

        print("Status update CSV loaded successfully into memory.")
        print(f"Detected delimiter: {repr(delimiter)}")
        print(f"Headers found: {len(headers)}")
        print(f"Total rows loaded: {total_rows}")

        batch_logger.info(
            f"CSV loaded into memory | "
            f"Delimiter={repr(delimiter)} | "
            f"Headers={len(headers)} | "
            f"Total Rows={total_rows}"
        )

        validator = StatusUpdateValidator(
            allowed_status_values=status_update_config["allowed_status_values"]
        )

        header_validation = validator.validate_headers(headers)

        if not header_validation["is_valid"]:
            print("Header validation failed.")
            print(f"Missing headers: {header_validation['missing_headers']}")

            batch_logger.error(
                f"Header validation failed | "
                f"Missing Headers={header_validation['missing_headers']} | "
                f"Unexpected Headers={header_validation['unexpected_headers']}"
            )

            continue

        if header_validation["unexpected_headers"]:
            print(f"Unexpected headers found: {header_validation['unexpected_headers']}")

            batch_logger.error(
                f"Unexpected headers found | "
                f"Unexpected Headers={header_validation['unexpected_headers']}"
            )

            continue

        print(f"\nValidating status update rows for file: {file_name}")

        validation_result = validator.validate_rows(rows)

        valid_rows = validation_result["valid_rows"]
        invalid_rows = validation_result["invalid_rows"]

        print("Status update validation completed.")
        print(f"Valid rows: {validation_result['total_valid']}")
        print(f"Invalid rows: {validation_result['total_invalid']}")

        batch_logger.info(
            f"Validation completed | "
            f"Valid Rows={validation_result['total_valid']} | "
            f"Invalid Rows={validation_result['total_invalid']}"
        )

        if invalid_rows:
            print("\nInvalid Status Update Details:")

            for invalid_row in invalid_rows:
                print(
                    f"Row={invalid_row.get('_row_number')} | "
                    f"UUID={invalid_row.get('uuid', 'N/A')} | "
                    f"accountStatus={invalid_row.get('accountStatus', 'N/A')} | "
                    f"ErrorCode={invalid_row.get('ErrorCode')} | "
                    f"ErrorDescription={invalid_row.get('ErrorDescription')}"
                )

        print(f"\nStarting SCIM status updates for file: {file_name}")

        scim_client = SCIMClient(
            create_user_url=target["create_user_url"],
            delete_user_url=target["delete_user_url"],
            auth_type=auth_config["auth_type"],
            username=auth_config["username"],
            password=auth_config["password"],
            timeout_seconds=http_config["request_timeout_seconds"],
            verify_ssl=http_config["verify_ssl"]
        )

        status_update_engine = StatusUpdateEngine(
            scim_client=scim_client,
            account_status_path=status_update_config["patch_account_status_path"],
            logger=batch_logger
        )

        update_result = status_update_engine.process_status_updates(valid_rows)

        successful_rows = update_result["successful_rows"]

        failed_rows = (
            invalid_rows
            + update_result["failed_rows"]
        )

        print("SCIM status update processing completed.")
        print(f"Successful updates: {len(successful_rows)}")
        print(f"Failed updates: {len(failed_rows)}")

        if successful_rows:
            print("\nSuccessful Status Update Details:")
            for success_row in successful_rows:
                print(
                    f"UUID={success_row.get('uuid')} | "
                    f"accountStatus={success_row.get('accountStatus')} | "
                    f"Result={success_row.get('StatusUpdateResult')}"
                )

        if failed_rows:
            print("\nFailed Status Update Details:")
            for failed_row in failed_rows:
                print(
                    f"UUID={failed_row.get('uuid', 'N/A')} | "
                    f"accountStatus={failed_row.get('accountStatus', 'N/A')} | "
                    f"ErrorCode={failed_row.get('ErrorCode')} | "
                    f"ErrorDescription={failed_row.get('ErrorDescription')}"
                )

        print(f"\nGenerating status update output files for: {file_name}")

        writer = StatusUpdateWriter(
            destination_dir=paths["destination_dir"]
        )

        success_file_result = writer.write_success_file(
            file_name=file_name,
            successful_rows=successful_rows
        )

        error_file_result = writer.write_error_file(
            file_name=file_name,
            failed_rows=failed_rows
        )

        if success_file_result["created"]:
            print(
                f"Success file created: {success_file_result['file_path']} | "
                f"Records: {success_file_result['record_count']}"
            )
        else:
            print("Success file not created because there are no successful updates.")

        if error_file_result["created"]:
            print(
                f"Error file created: {error_file_result['file_path']} | "
                f"Records: {error_file_result['record_count']}"
            )
        else:
            print("Error file not created because there are no failed updates.")

        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        status_update_tracker.record_status_update_result(
            status_update_file_name=file_name,
            sequence_number=file_info["sequence_number"],
            total_success=len(successful_rows),
            total_failed=len(failed_rows),
            started_at=started_at,
            completed_at=completed_at
        )

        print(f"\nStatus update tracker updated for file: {file_name}")

        batch_logger.info(
            f"Output file generation completed | "
            f"Success File Created={success_file_result['created']} | "
            f"Success Records={success_file_result['record_count']} | "
            f"Error File Created={error_file_result['created']} | "
            f"Error Records={error_file_result['record_count']}"
        )

        batch_logger.info(
            f"Status update processing completed | "
            f"Started At={started_at} | "
            f"Completed At={completed_at} | "
            f"Successful Updates={len(successful_rows)} | "
            f"Failed Updates={len(failed_rows)}"
        )

        batch_logger.info("=" * 80)


if __name__ == "__main__":
    main()