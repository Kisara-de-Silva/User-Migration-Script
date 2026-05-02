class UserValidator:
    def __init__(self, mandatory_fields, true_values, false_values):
        self.mandatory_fields = mandatory_fields
        self.true_values = true_values
        self.false_values = false_values

    def normalize_is_corp_user(self, value):
        if value is None:
            return None

        cleaned_value = str(value).strip().lower()

        if cleaned_value in self.true_values:
            return True

        if cleaned_value in self.false_values:
            return False

        return None

    def validate_user(self, user):
        errors = []

        for field in self.mandatory_fields:
            if not user.get(field, "").strip():
                errors.append({
                    "code": "ERR_001",
                    "description": f"Missing mandatory field: {field}"
                })

        is_corp_user_raw = user.get("isCorpUser", "")
        is_corp_user = self.normalize_is_corp_user(is_corp_user_raw)

        if is_corp_user is None:
            errors.append({
                "code": "ERR_003",
                "description": "Invalid User Type: isCorpUser must be a valid boolean value"
            })

        if is_corp_user is True:
            cifnumber = user.get("cifnumber", "").strip()

            if not cifnumber:
                errors.append({
                    "code": "ERR_001",
                    "description": "Missing mandatory field: cifnumber is required for corporate users"
                })

        if errors:
            error_codes = " | ".join(error["code"] for error in errors)
            error_descriptions = " | ".join(error["description"] for error in errors)

            invalid_user = user.copy()
            invalid_user["ErrorCode"] = error_codes
            invalid_user["ErrorDescription"] = error_descriptions

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
            result = self.validate_user(user)

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