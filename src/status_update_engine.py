import json


class StatusUpdateEngine:
    def __init__(self, scim_client, account_status_path="CombankDetails:accountStatus", logger=None):
        self.scim_client = scim_client
        self.account_status_path = account_status_path
        self.logger = logger

    def log_transaction(self, row_uuid, account_status, result):
        if not self.logger:
            return

        self.logger.info("----- STATUS UPDATE TRANSACTION START -----")
        self.logger.info(f"UUID: {row_uuid}")
        self.logger.info(f"Target Account Status: {account_status}")
        self.logger.info(f"System Response: HTTP_{result.get('status_code')}")
        self.logger.info(
            f"Patch Payload: {json.dumps(result.get('patch_payload', {}), ensure_ascii=False)}"
        )

        if result["success"]:
            self.logger.info("[SUCCESS] - Account status updated successfully.")
        else:
            self.logger.info(
                f"[FAILED] - {result.get('error_code')} | {result.get('error_description')}"
            )

        self.logger.info("----- STATUS UPDATE TRANSACTION END -----")

    def process_status_updates(self, valid_rows):
        successful_rows = []
        failed_rows = []

        for row in valid_rows:
            row_uuid = row.get("uuid", "").strip()
            account_status = row.get("_account_status_normalized", row.get("accountStatus", "")).strip()

            result = self.scim_client.update_account_status(
                user_uuid=row_uuid,
                account_status=account_status,
                account_status_path=self.account_status_path
            )

            self.log_transaction(row_uuid, account_status, result)

            if result["success"]:
                success_row = {
                    "uuid": row_uuid,
                    "accountStatus": account_status,
                    "StatusUpdateResult": "SUCCESS"
                }
                successful_rows.append(success_row)
            else:
                failed_row = {
                    "uuid": row_uuid,
                    "accountStatus": account_status,
                    "ErrorCode": result.get("error_code", "ERR_005"),
                    "ErrorDescription": result.get(
                        "error_description",
                        "Status update failed due to an unknown system error"
                    )
                }
                failed_rows.append(failed_row)

        return {
            "successful_rows": successful_rows,
            "failed_rows": failed_rows,
            "total_success": len(successful_rows),
            "total_failed": len(failed_rows)
        }