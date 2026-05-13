from datetime import datetime


class UserValidator:
    DATE_FIELDS = {
        "effectivefrom",
        "modifiedon",
        "checkedon",
        "lastPasswordChangeOn",
        "lockedTimestamp"
    }

    NUMERIC_FIELDS = {
        "noOfLoginAttempts",
        "noOfOTPAttempts",
        "noOfOtpGenerates"
    }

    ALLOWED_ACCOUNT_STATUSES = {
        "ACT",
        "ALK",
        "DBLT",
        "DBLP",
        "LCK",
        "UC"
    }

    BOOLEAN_FIELDS = {
        "isCorpUser",
        "isApprovalRequired",
        "forcePasswordChange"
    }

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

    def normalize_boolean(self, value):
        if value is None:
            return None

        cleaned_value = str(value).strip().lower()

        if cleaned_value in self.true_values:
            return True

        if cleaned_value in self.false_values:
            return False

        return None

    def is_valid_mmddyyyy_date(self, value):
        value = str(value).strip()

        if not value:
            return True

        try:
            datetime.strptime(value, "%m/%d/%Y")
            return True
        except ValueError:
            return False

    def is_valid_numeric(self, value):
        value = str(value).strip()

        if not value:
            return True

        return value.isdigit()

    def build_invalid_user(self, user, errors):
        unique_error_codes = []

        for error in errors:
            if error["code"] not in unique_error_codes:
                unique_error_codes.append(error["code"])

        error_codes = " | ".join(unique_error_codes)
        error_descriptions = " | ".join(error["description"] for error in errors)

        invalid_user = user.copy()
        invalid_user["ErrorCode"] = error_codes
        invalid_user["ErrorDescription"] = error_descriptions

        return invalid_user

    def validate_single_user(self, user):
        errors = []

        # ERR_001 - Missing mandatory fields
        for field in self.mandatory_fields:
            value = user.get(field, "")

            if value is None:
                value = ""

            if not str(value).strip():
                errors.append({
                    "code": "ERR_001",
                    "description": f"Missing mandatory field: {field}"
                })

        # ERR_001 - telno format
        telno = user.get("telno", "")

        if telno is not None and str(telno).strip():
            if not str(telno).strip().startswith("+"):
                errors.append({
                    "code": "ERR_001",
                    "description": "Invalid value for telno: phone number must start with +"
                })

        # ERR_001 - email format
        emailid = user.get("emailid", "")

        if emailid is not None and str(emailid).strip():
            if "@" not in str(emailid).strip():
                errors.append({
                    "code": "ERR_001",
                    "description": "Invalid value for emailid: email must contain @"
                })

        # ERR_001 - locationid numeric check
        locationid = user.get("locationid", "")

        if locationid is not None and str(locationid).strip():
            if not str(locationid).strip().isdigit():
                errors.append({
                    "code": "ERR_001",
                    "description": "Invalid numeric value for locationid"
                })

        # ERR_001 - corporateid numeric check
        # Important: we only validate it as digits. We do not convert it to int,
        # so leading zeros are preserved.
        corporateid = user.get("corporateid", "")

        if corporateid is not None and str(corporateid).strip():
            if not str(corporateid).strip().isdigit():
                errors.append({
                    "code": "ERR_001",
                    "description": "Invalid numeric value for corporateid"
                })

        # ERR_007 - accountStatus allowed values
        account_status = user.get("accountStatus", "")

        if account_status is not None and str(account_status).strip():
            cleaned_account_status = str(account_status).strip().upper()

            if cleaned_account_status not in self.ALLOWED_ACCOUNT_STATUSES:
                errors.append({
                    "code": "ERR_007",
                    "description": (
                        "Invalid value for accountStatus: allowed values are "
                        "ACT, ALK, DBLT, DBLP, LCK, UC"
                    )
                })

        # ERR_003 - Boolean fields
        normalized_boolean_values = {}

        for field in self.BOOLEAN_FIELDS:
            value = user.get(field, "")

            if value is not None and str(value).strip():
                normalized_value = self.normalize_boolean(value)

                if normalized_value is None:
                    errors.append({
                        "code": "ERR_003",
                        "description": (
                            f"Invalid boolean value for {field}: "
                            "allowed values are TRUE or FALSE"
                        )
                    })
                else:
                    normalized_boolean_values[field] = normalized_value

        # ERR_006 - Date format validation
        for field in self.DATE_FIELDS:
            value = user.get(field, "")

            if value and not self.is_valid_mmddyyyy_date(value):
                errors.append({
                    "code": "ERR_006",
                    "description": f"Invalid date format for {field}: expected MM/DD/YYYY"
                })

        # ERR_001 - Numeric attempt fields
        for field in self.NUMERIC_FIELDS:
            value = user.get(field, "")

            if value and not self.is_valid_numeric(value):
                errors.append({
                    "code": "ERR_001",
                    "description": f"Invalid numeric value for {field}"
                })

        is_corp_user = normalized_boolean_values.get("isCorpUser")

        if errors:
            invalid_user = self.build_invalid_user(user, errors)

            if is_corp_user is not None:
                invalid_user["_is_corp_user_normalized"] = is_corp_user

            return {
                "is_valid": False,
                "user": invalid_user
            }

        valid_user = user.copy()
        valid_user["_is_corp_user_normalized"] = is_corp_user

        return {
            "is_valid": True,
            "user": valid_user
        }

    def validate_users(self, users):
        valid_users = []
        invalid_users = []

        for user in users:
            result = self.validate_single_user(user)

            if result["is_valid"]:
                valid_users.append(result["user"])
            else:
                invalid_users.append(result["user"])

        return {
            "valid_users": valid_users,
            "invalid_users": invalid_users,
            "total_valid": len(valid_users),
            "total_invalid": len(invalid_users)
        }