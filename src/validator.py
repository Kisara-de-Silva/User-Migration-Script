class UserValidator:
    def __init__(self, mandatory_fields, true_values, false_values, expected_headers=None):
        self.mandatory_fields = mandatory_fields
        self.true_values = true_values
        self.false_values = false_values
        self.expected_headers = expected_headers or []

    def validate_headers(self, headers):
        missing_headers = []

        for expected_header in self.expected_headers:
            if expected_header not in headers:
                missing_headers.append(expected_header)

        unexpected_headers = []

        for header in headers:
            if self.expected_headers and header not in self.expected_headers:
                unexpected_headers.append(header)

        return {
            "is_valid": len(missing_headers) == 0,
            "missing_headers": missing_headers,
            "unexpected_headers": unexpected_headers
        }

    def normalize_is_corp_user(self, value):
        if value is None:
            return None

        cleaned_value = str(value).strip().lower()

        if cleaned_value in self.true_values:
            return True

        if cleaned_value in self.false_values:
            return False

        return None

    def build_invalid_user(self, user, errors):
        error_codes = " | ".join(error["code"] for error in errors)
        error_descriptions = " | ".join(error["description"] for error in errors)

        invalid_user = user.copy()
        invalid_user["ErrorCode"] = error_codes
        invalid_user["ErrorDescription"] = error_descriptions

        return invalid_user

    def validate_single_user(self, user):
        errors = []

        for field in self.mandatory_fields:
            value = user.get(field, "")

            if value is None:
                value = ""

            if not str(value).strip():
                errors.append({
                    "code": "ERR_001",
                    "description": f"Missing mandatory field: {field}"
                })

        telno = user.get("telno", "")

        if telno is not None and str(telno).strip():
            if not str(telno).strip().startswith("+"):
                errors.append({
                    "code": "ERR_001",
                    "description": "Invalid value for telno: phone number must start with +"
                })

        emailid = user.get("emailid", "")

        if emailid is not None and str(emailid).strip():
            if "@" not in str(emailid).strip():
                errors.append({
                    "code": "ERR_001",
                    "description": "Invalid value for emailid: email must contain @"
                })

        is_corp_user_raw = user.get("isCorpUser", "")
        is_corp_user = None

        if is_corp_user_raw is not None and str(is_corp_user_raw).strip():
            is_corp_user = self.normalize_is_corp_user(is_corp_user_raw)

            if is_corp_user is None:
                errors.append({
                    "code": "ERR_003",
                    "description": "Invalid User Type: isCorpUser must be a valid boolean value"
                })

        if errors:
            invalid_user = self.build_invalid_user(user, errors)

            if is_corp_user is not None:
                invalid_user["_is_corp_user_normalized"] = is_corp_user

            return {
                "is_valid": False,
                "user": invalid_user,
                "cifnumber": user.get("cifnumber", "").strip()
            }

        valid_user = user.copy()
        valid_user["_is_corp_user_normalized"] = is_corp_user

        return {
            "is_valid": True,
            "user": valid_user,
            "cifnumber": user.get("cifnumber", "").strip()
        }

    def validate_users(self, users):
        initial_results = []
        failed_cifs = {}

        for user in users:
            result = self.validate_single_user(user)
            initial_results.append(result)

            cifnumber = result["cifnumber"]

            if not result["is_valid"] and cifnumber:
                failed_loginid = result["user"].get("loginid", "UNKNOWN")
                failed_cifs[cifnumber] = failed_loginid

        valid_users = []
        invalid_users = []
        cif_rejected_users = 0

        for result in initial_results:
            user = result["user"]
            cifnumber = result["cifnumber"]

            if result["is_valid"] and cifnumber in failed_cifs:
                failed_user = user.copy()
                failed_user["ErrorCode"] = "ERR_002"
                failed_user["ErrorDescription"] = (
                    f"CIF Group Failure Rollback. CIF {cifnumber} failed "
                    f"because user {failed_cifs[cifnumber]} failed validation."
                )

                invalid_users.append(failed_user)
                cif_rejected_users += 1

            elif result["is_valid"]:
                valid_users.append(user)

            else:
                invalid_users.append(user)

        return {
            "valid_users": valid_users,
            "invalid_users": invalid_users,
            "total_valid": len(valid_users),
            "total_invalid": len(invalid_users),
            "failed_cifs": failed_cifs,
            "cif_rejected_users": cif_rejected_users
        }