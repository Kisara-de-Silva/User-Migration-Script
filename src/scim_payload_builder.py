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

    def build_payload(self, user):
        original_loginid = self.get_value(user, "loginid")
        uppercase_loginid = original_loginid.upper()

        user_uuid = self.get_value(user, "uuid")

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
                    "value": self.get_value(user, "telno"),
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
                "cif": self.get_value(user, "cifnumber"),
                "loginId": uppercase_loginid,
                "activateDate": self.get_value(user, "effectivefrom"),
                "identificationType": self.get_value(user, "identificationtype"),
                "lockedUser": self.get_value(user, "lockedUser"),
                "createdOn": self.get_value(user, "effectivefrom"),
                "isApprovalRequired": self.to_boolean(user, "isApprovalRequired"),
                "accountStatus": self.get_value(user, "accountStatus"),
                "lockStatus": None,
                "lastPasswordChangeOn": self.get_value(user, "lastPasswordChangeOn"),
                "isMigrated": self.to_boolean(user, "ismigrated"),
                "unifiedUsername": original_loginid,
                "migratedUsername": original_loginid,
                "lockedTimestamp": None,
                "noOfOTPAttempts": 0,
                "noOfOtpGenerates": 0,
                "customStr03": None,
                "customStr02": None,
                "lockedReason": self.get_value(user, "lockedReason"),
                "customStr01": None,
                "updatedBy": self.get_value(user, "modifiedby"),
                "isCorpUser": self.to_boolean(user, "isCorpUser"),
                "customStr05": None,
                "customStr04": None,
                "updatedOn": self.get_value(user, "modifiedon"),
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