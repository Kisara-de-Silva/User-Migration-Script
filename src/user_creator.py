import uuid

from src.scim_payload_builder import SCIMPayloadBuilder
from src.scim_client import SCIMClient


class UserCreator:
    def __init__(
        self,
        create_user_url,
        delete_user_url,
        mock_mode=True,
        true_values=None,
        false_values=None,
        scim_payload_config=None,
        auth_config=None,
        http_config=None
    ):
        self.create_user_url = create_user_url
        self.delete_user_url = delete_user_url
        self.mock_mode = mock_mode

        true_values = true_values or ["true", "yes", "1", "y"]
        false_values = false_values or ["false", "no", "0", "n"]
        scim_payload_config = scim_payload_config or {}
        auth_config = auth_config or {}
        http_config = http_config or {}

        self.scim_payload_builder = SCIMPayloadBuilder(
            true_values=true_values,
            false_values=false_values,
            native_password=scim_payload_config.get("native_password", "admin"),
            preferred_language=scim_payload_config.get("preferred_language", "SG"),
            created_by=scim_payload_config.get("created_by", "migrationScript"),
            mfa_config=scim_payload_config.get(
                "mfa_config",
                '{"SMS": true, "EMAIL": true, "SOFT_TOKEN": false, "FIDO": false}'
            )
        )

        self.scim_client = SCIMClient(
            create_user_url=create_user_url,
            delete_user_url=delete_user_url,
            auth_type=auth_config.get("auth_type", "BASIC"),
            username=auth_config.get("username", ""),
            password=auth_config.get("password", ""),
            timeout_seconds=http_config.get("request_timeout_seconds", 30),
            verify_ssl=http_config.get("verify_ssl", True)
        )

    def build_output_user(self, user):
        output_user = {}

        excluded_fields = {
            "ErrorCode",
            "ErrorDescription"
        }

        for key, value in user.items():
            if key.startswith("_"):
                continue

            if key in excluded_fields:
                continue

            output_user[key] = value

        if not output_user.get("uuid"):
            output_user["uuid"] = str(uuid.uuid4())

        return output_user

    def create_user(self, user):
        output_user = self.build_output_user(user)
        api_payload = self.scim_payload_builder.build_payload(output_user)

        loginid = output_user.get("loginid", "").strip()

        if self.mock_mode:
            if "fail" in loginid.lower():
                return {
                    "success": False,
                    "loginid": loginid,
                    "payload": output_user,
                    "api_payload": api_payload,
                    "system_response_code": "MOCK_500",
                    "error_code": "ERR_005",
                    "error_description": "Mock user creation failure"
                }

            return {
                "success": True,
                "loginid": loginid,
                "payload": output_user,
                "api_payload": api_payload,
                "system_response_code": "MOCK_201",
                "uuid": output_user["uuid"]
            }

        scim_result = self.scim_client.create_user(api_payload)

        if scim_result["success"]:
            return {
                "success": True,
                "loginid": loginid,
                "payload": output_user,
                "api_payload": api_payload,
                "system_response_code": f"HTTP_{scim_result['status_code']}",
                "uuid": output_user["uuid"],
                "scim_response": scim_result.get("response_body")
            }

        return {
            "success": False,
            "loginid": loginid,
            "payload": output_user,
            "api_payload": api_payload,
            "system_response_code": f"HTTP_{scim_result['status_code']}",
            "error_code": scim_result["error_code"],
            "error_description": scim_result["error_description"],
            "scim_response": scim_result.get("response_body")
        }

    def delete_user(self, loginid, user_uuid=None):
        if self.mock_mode:
            return {
                "success": True,
                "loginid": loginid,
                "system_response_code": "MOCK_DELETE_200"
            }

        if not user_uuid:
            return {
                "success": False,
                "loginid": loginid,
                "system_response_code": "NO_UUID",
                "error_code": "ERR_005",
                "error_description": "Cannot rollback user because uuid is missing"
            }

        scim_result = self.scim_client.delete_user(user_uuid)

        if scim_result["success"]:
            return {
                "success": True,
                "loginid": loginid,
                "uuid": user_uuid,
                "system_response_code": f"HTTP_{scim_result['status_code']}",
                "delete_url": scim_result.get("delete_url")
            }

        return {
            "success": False,
            "loginid": loginid,
            "uuid": user_uuid,
            "system_response_code": f"HTTP_{scim_result['status_code']}",
            "delete_url": scim_result.get("delete_url"),
            "error_code": scim_result["error_code"],
            "error_description": scim_result["error_description"]
        }