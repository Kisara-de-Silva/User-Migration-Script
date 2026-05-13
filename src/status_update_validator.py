import uuid


class StatusUpdateValidator:
    EXPECTED_HEADERS = ["uuid", "accountStatus"]

    def __init__(self, allowed_status_values):
        self.allowed_status_values = {
            value.strip().upper()
            for value in allowed_status_values
        }

    def validate_headers(self, headers):
        missing_headers = []

        for expected_header in self.EXPECTED_HEADERS:
            if expected_header not in headers:
                missing_headers.append(expected_header)

        unexpected_headers = []

        for header in headers:
            if header not in self.EXPECTED_HEADERS:
                unexpected_headers.append(header)

        return {
            "is_valid": len(missing_headers) == 0,
            "missing_headers": missing_headers,
            "unexpected_headers": unexpected_headers
        }

    def is_valid_uuid_format(self, value):
        try:
            uuid.UUID(str(value).strip())
            return True
        except ValueError:
            return False

    def validate_row(self, row):
        errors = []

        row_uuid = row.get("uuid", "").strip()
        account_status = row.get("accountStatus", "").strip()

        if not row_uuid:
            errors.append({
                "code": "ERR_001",
                "description": "Missing mandatory field: uuid"
            })
        elif not self.is_valid_uuid_format(row_uuid):
            errors.append({
                "code": "ERR_001",
                "description": "Invalid uuid format"
            })

        if not account_status:
            errors.append({
                "code": "ERR_001",
                "description": "Missing mandatory field: accountStatus"
            })
        else:
            normalized_status = account_status.upper()

            if normalized_status not in self.allowed_status_values:
                errors.append({
                    "code": "ERR_007",
                    "description": (
                        "Invalid value for accountStatus: allowed values are "
                        + ", ".join(sorted(self.allowed_status_values))
                    )
                })

        if errors:
            invalid_row = row.copy()
            invalid_row["ErrorCode"] = " | ".join(
                dict.fromkeys(error["code"] for error in errors)
            )
            invalid_row["ErrorDescription"] = " | ".join(
                error["description"] for error in errors
            )

            return {
                "is_valid": False,
                "row": invalid_row
            }

        valid_row = row.copy()
        valid_row["_account_status_normalized"] = account_status.upper()

        return {
            "is_valid": True,
            "row": valid_row
        }

    def validate_rows(self, rows):
        valid_rows = []
        invalid_rows = []

        for row in rows:
            result = self.validate_row(row)

            if result["is_valid"]:
                valid_rows.append(result["row"])
            else:
                invalid_rows.append(result["row"])

        return {
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "total_valid": len(valid_rows),
            "total_invalid": len(invalid_rows)
        }