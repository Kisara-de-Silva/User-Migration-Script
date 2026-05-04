import json


class MigrationEngine:
    SENSITIVE_FIELDS = {
        "password",
        "digestedpassword",
        "newpassword",
        "oldpassword",
        "secret",
        "token",
        "nationalidcardorpassport",
        "telno",
        "emailid"
    }

    def __init__(self, user_creator, logger=None):
        self.user_creator = user_creator
        self.logger = logger

    def sanitize_payload(self, payload):
        sanitized_payload = {}

        for key, value in payload.items():
            if key.lower() in self.SENSITIVE_FIELDS:
                sanitized_payload[key] = "***MASKED***"
            else:
                sanitized_payload[key] = value

        return sanitized_payload

    def log_transaction(self, loginid, payload, system_response_code, status, description):
        if not self.logger:
            return

        sanitized_payload = self.sanitize_payload(payload)

        self.logger.info("----- USER TRANSACTION START -----")
        self.logger.info(f"User Identifier: {loginid}")
        self.logger.info(f"Payload Data: {json.dumps(sanitized_payload, ensure_ascii=False)}")
        self.logger.info(f"System Response: {system_response_code}")
        self.logger.info(f"[{status}] - {description}")
        self.logger.info("----- USER TRANSACTION END -----")

    def process_retail_users(self, retail_users):
        successful_users = []
        failed_users = []

        for user in retail_users:
            result = self.user_creator.create_user(user)

            if result["success"]:
                success_user = result["payload"].copy()
                success_user["_creation_status"] = "SUCCESS"
                success_user["_system_response_code"] = result["system_response_code"]
                successful_users.append(success_user)

                self.log_transaction(
                    loginid=result["loginid"],
                    payload=result["payload"],
                    system_response_code=result["system_response_code"],
                    status="SUCCESS",
                    description="Retail user successfully generated."
                )

            else:
                failed_user = user.copy()
                failed_user["ErrorCode"] = result["error_code"]
                failed_user["ErrorDescription"] = result["error_description"]
                failed_users.append(failed_user)

                self.log_transaction(
                    loginid=result["loginid"],
                    payload=result["payload"],
                    system_response_code=result["system_response_code"],
                    status="FAILED",
                    description=result["error_description"]
                )

        return {
            "successful_users": successful_users,
            "failed_users": failed_users
        }

    def process_corporate_cif_groups(self, corporate_cif_groups):
        successful_users = []
        failed_users = []
        rollback_count = 0

        for cifnumber, users_in_cif in corporate_cif_groups.items():
            if self.logger:
                self.logger.info(f"Starting corporate CIF group processing | CIF={cifnumber} | Users={len(users_in_cif)}")

            created_users_in_group = []
            group_failed = False
            failed_result = None

            for user in users_in_cif:
                result = self.user_creator.create_user(user)

                if result["success"]:
                    created_users_in_group.append(result)

                    self.log_transaction(
                        loginid=result["loginid"],
                        payload=result["payload"],
                        system_response_code=result["system_response_code"],
                        status="SUCCESS",
                        description=f"Corporate user successfully generated under CIF {cifnumber}."
                    )

                else:
                    group_failed = True
                    failed_result = result

                    self.log_transaction(
                        loginid=result["loginid"],
                        payload=result["payload"],
                        system_response_code=result["system_response_code"],
                        status="FAILED",
                        description=result["error_description"]
                    )

                    break

            if group_failed:
                failed_loginid = failed_result.get("loginid", "UNKNOWN")

                if self.logger:
                    self.logger.info(
                        f"CIF group failure detected | CIF={cifnumber} | "
                        f"Failed LoginID={failed_loginid} | Starting rollback"
                    )

                for created_result in created_users_in_group:
                    rollback_loginid = created_result.get("loginid")
                    rollback_result = self.user_creator.delete_user(rollback_loginid)
                    rollback_count += 1

                    self.log_transaction(
                        loginid=rollback_loginid,
                        payload=created_result["payload"],
                        system_response_code=rollback_result["system_response_code"],
                        status="ROLLBACK",
                        description=f"User creation reversed due to CIF group failure. CIF={cifnumber}."
                    )

                for user in users_in_cif:
                    failed_user = user.copy()

                    if user.get("loginid") == failed_loginid:
                        failed_user["ErrorCode"] = failed_result["error_code"]
                        failed_user["ErrorDescription"] = failed_result["error_description"]
                    else:
                        failed_user["ErrorCode"] = "ERR_002"
                        failed_user["ErrorDescription"] = (
                            f"CIF Group Failure Rollback. CIF {cifnumber} failed "
                            f"because user {failed_loginid} failed creation."
                        )

                    failed_users.append(failed_user)

            else:
                if self.logger:
                    self.logger.info(f"Corporate CIF group completed successfully | CIF={cifnumber}")

                for created_result in created_users_in_group:
                    success_user = created_result["payload"].copy()
                    success_user["_creation_status"] = "SUCCESS"
                    success_user["_system_response_code"] = created_result["system_response_code"]
                    successful_users.append(success_user)

        return {
            "successful_users": successful_users,
            "failed_users": failed_users,
            "rollback_count": rollback_count
        }