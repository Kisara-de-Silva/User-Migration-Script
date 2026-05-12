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

        for field in self.DATE_FIELDS:
            value = user.get(field, "")

            if value and not self.is_valid_mmddyyyy_date(value):
                errors.append({
                    "code": "ERR_001",
                    "description": f"Invalid date format for {field}: expected MM/DD/YYYY"
                })

        for field in self.NUMERIC_FIELDS:
            value = user.get(field, "")

            if value and not self.is_valid_numeric(value):
                errors.append({
                    "code": "ERR_001",
                    "description": f"Invalid numeric value for {field}"
                })

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