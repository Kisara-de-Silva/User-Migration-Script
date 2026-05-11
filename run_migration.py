from datetime import datetime
from src.config_loader import ConfigLoader
from src.batch_detector import BatchDetector
from src.tracker import MigrationTracker
from src.csv_loader import CSVLoader
from src.validator import UserValidator
from src.processor import UserProcessor
from src.user_creator import UserCreator
from src.migration_engine import MigrationEngine
from src.file_writer import FileWriter
from src.logger_setup import setup_batch_logger


def main():
    config_loader = ConfigLoader()
    config_loader.load_config()

    paths = config_loader.get_paths()
    target = config_loader.get_target_config()
    batch_config = config_loader.get_batch_config()
    validation_config = config_loader.get_validation_config()
    execution_config = config_loader.get_execution_config()
    output_config = config_loader.get_output_config()
    scim_payload_config = config_loader.get_scim_payload_config()
    auth_config = config_loader.get_auth_config()
    http_config = config_loader.get_http_config()

    print("Configuration loaded successfully.")
    print("Paths:", paths)
    print("Target:", target)
    print("Batch Config:", batch_config)
    print("Validation Config:", validation_config)
    print("Execution Config:", execution_config)
    print("Output Config:", output_config)
    print("SCIM Payload Config:", {
        "native_password": "***MASKED***",
        "preferred_language": scim_payload_config["preferred_language"],
        "created_by": scim_payload_config["created_by"],
        "mfa_config": "configured"
    })
    print("Auth Config:", {
        "auth_type": auth_config["auth_type"],
        "username": auth_config["username"],
        "password": "***MASKED***"
    })
    print("HTTP Config:", http_config)

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

        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        batch_logger = setup_batch_logger(
            log_dir=paths["log_dir"],
            batch_file_name=batch_file_name
        )

        batch_logger.info("=" * 80)
        batch_logger.info(f"Batch processing started | Batch={batch_file_name}")
        batch_logger.info(f"Sequence Number={batch['sequence_number']}")
        batch_logger.info(f"Source File={batch['file_path']}")
        batch_logger.info(f"Target Create URL={target['create_user_url']}")
        batch_logger.info(f"Mock Mode={execution_config['mock_mode']}")

        print(f"\nLoading CSV data into memory for batch: {batch_file_name}")

        csv_loader = CSVLoader(batch["file_path"])
        csv_data = csv_loader.load_users_to_memory()

        headers = csv_data["headers"]
        users = csv_data["users"]
        total_users = csv_data["total_users"]
        delimiter = csv_data["delimiter"]
        ignored_columns = csv_data["ignored_columns"]

        print("CSV loaded successfully into memory.")
        print(f"Detected delimiter: {repr(delimiter)}")
        print(f"Headers found: {len(headers)}")
        print(f"Total users loaded: {total_users}")

        if ignored_columns:
            print(f"Ignored system columns: {ignored_columns}")

        if total_users > 0:
            first_user = users[0]
            print(
                "First user sample: "
                f"Row={first_user.get('_row_number')} | "
                f"LoginID={first_user.get('loginid', 'N/A')} | "
                f"isCorpUser={first_user.get('isCorpUser', 'N/A')} | "
                f"CIF={first_user.get('cifnumber', 'N/A')}"
            )

        batch_logger.info(
            f"CSV loaded into memory | "
            f"Delimiter={repr(delimiter)} | "
            f"Headers={len(headers)} | "
            f"Total Users={total_users} |"
            f"Ignored System Columns={ignored_columns}"
        )

        print(f"\nValidating users for batch: {batch_file_name}")

        validator = UserValidator(
            mandatory_fields=validation_config["mandatory_fields"],
            true_values=validation_config["true_values"],
            false_values=validation_config["false_values"], 
            expected_headers=validation_config["expected_headers"]
        )

        header_validation_result = validator.validate_headers(headers)

        if not header_validation_result["is_valid"]:
            print("Header validation failed.")
            print(f"Missing headers: {header_validation_result['missing_headers']}")

            batch_logger.error(
                f"Header validation failed | "
                f"Missing Headers={header_validation_result['missing_headers']} | "
                f"Unexpected Headers={header_validation_result['unexpected_headers']}"
            )

            continue

        if header_validation_result["unexpected_headers"]:
            print(f"Unexpected headers found: {header_validation_result['unexpected_headers']}")

            batch_logger.warning(
                f"Unexpected headers found | "
                f"Unexpected Headers={header_validation_result['unexpected_headers']}"
            )

        validation_result = validator.validate_users(users)

        valid_users = validation_result["valid_users"]
        invalid_users = validation_result["invalid_users"]

        print("Validation completed.")
        print(f"Valid users: {validation_result['total_valid']}")
        print(f"Invalid users: {validation_result['total_invalid']}")
        print(f"CIF validation rejected users: {validation_result['cif_rejected_users']}")

        if validation_result["failed_cifs"]:
            print(f"Failed CIFs due to validation: {validation_result['failed_cifs']}")

        if invalid_users:
            print("\nInvalid User Details:")

            for invalid_user in invalid_users:
                print(
                    f"Row={invalid_user.get('_row_number')} | "
                    f"LoginID={invalid_user.get('loginid', 'N/A')} | "
                    f"ErrorCode={invalid_user.get('ErrorCode')} | "
                    f"ErrorDescription={invalid_user.get('ErrorDescription')}"
                )

        batch_logger.info(
            f"Validation completed | "
            f"Valid Users={validation_result['total_valid']} | "
            f"Invalid Users={validation_result['total_invalid']} | "
            f"CIF Rejected Users={validation_result['cif_rejected_users']} | "
            f"Failed CIFs={validation_result['failed_cifs']}"
        )

        print(f"\nSegregating valid users for batch: {batch_file_name}")

        processor = UserProcessor()

        segregation_result = processor.segregate_users(valid_users)

        retail_users = segregation_result["retail_users"]
        corporate_users = segregation_result["corporate_users"]

        print("User segregation completed.")
        print(f"Retail users: {segregation_result['total_retail_users']}")
        print(f"Corporate users: {segregation_result['total_corporate_users']}")

        corporate_cif_groups = processor.group_corporate_users_by_cif(corporate_users)

        print("\nCorporate CIF Groups:")

        if not corporate_cif_groups:
            print("No corporate CIF groups found.")
        else:
            for cifnumber, users_in_cif in corporate_cif_groups.items():
                print(
                    f"CIF={cifnumber} | "
                    f"Users in group: {len(users_in_cif)}"
                )

        batch_logger.info(
            f"User segregation completed | "
            f"Retail Users={segregation_result['total_retail_users']} | "
            f"Corporate Users={segregation_result['total_corporate_users']}"
        )

        if execution_config["mock_mode"]:
            print(f"\nStarting mock user creation for batch: {batch_file_name}")
        else:
            print(f"\nStarting real SCIM user creation for batch: {batch_file_name}")

        user_creator = UserCreator(
            create_user_url=target["create_user_url"],
            delete_user_url=target["delete_user_url"],
            mock_mode=execution_config["mock_mode"],
            true_values=validation_config["true_values"],
            false_values=validation_config["false_values"],
            scim_payload_config=scim_payload_config,
            auth_config=auth_config,
            http_config=http_config
        )

        migration_engine = MigrationEngine(
            user_creator=user_creator,
            logger=batch_logger
        )

        retail_result = migration_engine.process_retail_users(retail_users)
        corporate_result = migration_engine.process_corporate_cif_groups(corporate_cif_groups)

        successful_users = (
            retail_result["successful_users"]
            + corporate_result["successful_users"]
        )

        failed_users = (
            invalid_users
            + retail_result["failed_users"]
            + corporate_result["failed_users"]
        )

        if execution_config["mock_mode"]:
            print("Mock user creation completed.")
        else:
            print("Real SCIM user creation completed.")
            
        print(f"Successful users: {len(successful_users)}")
        print(f"Failed users: {len(failed_users)}")
        print(f"Rollback users: {corporate_result['rollback_count']}")

        if successful_users:
            print("\nSuccessful User Details:")
            for success_user in successful_users:
                print(
                    f"LoginID={success_user.get('loginid')} | "
                    f"UUID={success_user.get('uuid')} | "
                    f"Status={success_user.get('_creation_status')}"
                )

        if failed_users:
            print("\nFailed User Details:")
            for failed_user in failed_users:
                print(
                    f"Row={failed_user.get('_row_number')} | "
                    f"LoginID={failed_user.get('loginid', 'N/A')} | "
                    f"ErrorCode={failed_user.get('ErrorCode')} | "
                    f"ErrorDescription={failed_user.get('ErrorDescription')}"
                )

        print(f"\nGenerating output files for batch: {batch_file_name}")

        file_writer = FileWriter(
            destination_dir=paths["destination_dir"],
            output_fields=output_config["output_fields"]
        )

        success_file_result = file_writer.write_success_file(
            batch_file_name=batch_file_name,
            successful_users=successful_users
        )

        error_file_result = file_writer.write_error_file(
            batch_file_name=batch_file_name,
            failed_users=failed_users
        )

        if success_file_result["created"]:
            print(
                f"Success file created: {success_file_result['file_path']} | "
                f"Records: {success_file_result['record_count']}"
            )
        else:
            print("Success file not created because there are no successful users.")

        if error_file_result["created"]:
            print(
                f"Error file created: {error_file_result['file_path']} | "
                f"Records: {error_file_result['record_count']}"
            )
        else:
            print("Error file not created because there are no failed users.")

        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        batch_logger.info(
            f"Output file generation completed | "
            f"Success File Created={success_file_result['created']} | "
            f"Success Records={success_file_result['record_count']} | "
            f"Error File Created={error_file_result['created']} | "
            f"Error Records={error_file_result['record_count']}"
        )

        tracker.record_batch_result(
            batch_file_name=batch_file_name,
            sequence_number=batch["sequence_number"],
            total_users_migrated=len(successful_users),
            total_users_failed=len(failed_users),
            started_at=started_at,
            completed_at=completed_at
        )

        print(f"\nTracker updated for batch: {batch_file_name}")

        batch_logger.info(
            f"Tracker updated | "
            f"Batch={batch_file_name} | "
            f"Sequence={batch['sequence_number']} | "
            f"Executed=true | "
            f"Total Migrated={len(successful_users)} | "
            f"Total Failed={len(failed_users)}"
        )

        batch_logger.info(
            f"Batch processing completed | "
            f"Started At={started_at} | "
            f"Completed At={completed_at} | "
            f"Successful Users={len(successful_users)} | "
            f"Failed Users={len(failed_users)} | "
            f"Rollback Users={corporate_result['rollback_count']}"
        )

        batch_logger.info("=" * 80)


if __name__ == "__main__":
    main()