from datetime import datetime


class SCIMPayloadBuilder:
    def __init__(
        self,
        true_values,
        false_values,
        native_password="admin",
        preferred_language="SG",
        created_by="migrationScript",
        mfa_config='{"SMS": true, "EMAIL": true, "SOFT_TOKEN": false, "FIDO": false}'
    ):
        self.true_values = true_values
        self.false_values = false_values
        self.native_password = native_password
        self.preferred_language = preferred_language
        self.created_by = created_by
        self.mfa_config = mfa_config

    def get_value(self, user, field_name):
        value = user.get(field_name, "")

        if value is None:
            return ""

        return str(value).strip()

    def to_boolean(self, user, field_name):
        value = self.get_value(user, field_name).lower()

        if value in self.true_values:
            return True

        if value in self.false_values:
            return False

        raise ValueError(f"Invalid boolean value for field: {field_name}")
    
    def get_telno_for_isds(self, user):
        telno = self.get_value(user, "telno")

        if not telno:
            return ""

        if telno.startswith("+"):
            return telno

        return f"+{telno}"

    def to_integer(self, user, field_name, default_value=0):
        value = self.get_value(user, field_name)

        if not value:
            return default_value

        return int(value)

    def convert_yyyy_mm_dd_to_isds_datetime(self, user, field_name):
        value = self.get_value(user, field_name)

        if not value:
            return ""

        # If already in ISDS format, keep it unchanged.
        # Example: 20250918120832Z
        if len(value) == 15 and value.endswith("Z") and value[:14].isdigit():
            return value

        parsed_date = datetime.strptime(value, "%Y-%m-%d")

        # BU input gives only date, so we use 000000 for time.
        return parsed_date.strftime("%Y%m%d000000Z")

    def build_payload(self, user):
        original_loginid = self.get_value(user, "loginid")
        uppercase_loginid = original_loginid.upper()

        user_uuid = self.get_value(user, "uuid")

        effective_from_isds = self.convert_yyyy_mm_dd_to_isds_datetime(user, "effectivefrom")
        modified_on_isds = self.convert_yyyy_mm_dd_to_isds_datetime(user, "modifiedon")
        last_password_change_on_isds = self.convert_yyyy_mm_dd_to_isds_datetime(
            user,
            "lastPasswordChangeOn"
        )

        return {
            "password": self.native_password,
            "addresses": [
                {
                    "streetAddress": None,
                    "formatted": None,
                    "postalCode": None,
                    "locality": None,
                    "type": "work",
                    "region": None
                },
                {
                    "formatted": None,
                    "type": "home"
                }
            ],
            "preferredLanguage": self.preferred_language,
            "displayName": self.get_value(user, "FullName"),
            "externalId": None,
            "title": None,
            "userName": user_uuid,
            "urn:ietf:params:scim:schemas:extension:isam:1.0:User": {
                "passwordValid": True,
                "identity": user_uuid,
                "accountValid": True
            },
            "phoneNumbers": [
                {
                    "type": "mobile",
                    "value": self.get_telno_for_isds(user),
                    "primary": False
                }
            ],
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
                "manager": {
                    "value": None
                },
                "organization": None,
                "department": None,
                "employeeNumber": None
            },
            "emails": [
                {
                    "type": "work",
                    "value": self.get_value(user, "emailid"),
                    "primary": True
                }
            ],
            "CombankDetails": {
                "cif": self.get_value(user, "corporateid"),
                "loginId": uppercase_loginid,
                "activateDate": effective_from_isds,
                "identificationType": self.get_value(user, "identificationtype"),
                "lockedUser": self.get_value(user, "lockedUser"),
                "createdOn": effective_from_isds,
                "isApprovalRequired": self.to_boolean(user, "isApprovalRequired"),
                "accountStatus": self.get_value(user, "accountStatus"),
                "lockStatus": None,
                "lastPasswordChangeOn": last_password_change_on_isds,
                "isMigrated": True,
                "unifiedUsername": original_loginid,
                "migratedUsername": original_loginid,
                "lockedTimestamp": None,
                "noOfOTPAttempts": self.to_integer(user, "noOfOTPAttempts", 0),
                "noOfOtpGenerates": self.to_integer(user, "noOfOtpGenerates", 0),
                "noOfLoginAttempts": self.to_integer(user, "noOfLoginAttempts", 0),
                "customStr03": None,
                "customStr02": None,
                "lockedReason": self.get_value(user, "lockedReason"),
                "customStr01": None,
                "updatedBy": self.get_value(user, "modifiedby"),
                "isCorpUser": self.to_boolean(user, "isCorpUser"),
                "customStr05": None,
                "customStr04": None,
                "updatedOn": modified_on_isds,
                "digestedPassword": self.get_value(user, "digestedPassword"),
                "createdBy": self.created_by,
                "mfaConfig": self.mfa_config,
                "forcePasswordChange": self.to_boolean(user, "forcePasswordChange"),
                "authorizeFlag": None,
                "identificationNumber": self.get_value(user, "nationalidcardorpassport"),
                "remarks": self.get_value(user, "Remarks"),
                "originSystem": self.get_value(user, "originSystem")
            },
            "schemas": [
                "urn:ietf:params:scim:schemas:core:2.0:User",
                "CombankDetails",
                "urn:ietf:params:scim:schemas:extension:isam:1.0:User",
                "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
            ],
            "name": {
                "givenName": self.get_value(user, "firstname"),
                "familyName": self.get_value(user, "lastname")
            }
        }