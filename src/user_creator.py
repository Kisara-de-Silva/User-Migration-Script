import uuid


class UserCreator:
    def __init__(self, create_user_url, delete_user_url, mock_mode=True):
        self.create_user_url = create_user_url
        self.delete_user_url = delete_user_url
        self.mock_mode = mock_mode

    def build_payload(self, user):
        payload = {}

        excluded_fields = {
            "ErrorCode",
            "ErrorDescription"
        }

        for key, value in user.items():
            if key.startswith("_"):
                continue

            if key in excluded_fields:
                continue

            payload[key] = value

        if not payload.get("uuid"):
            payload["uuid"] = str(uuid.uuid4())

        return payload

    def create_user(self, user):
        payload = self.build_payload(user)

        loginid = payload.get("loginid", "").strip()

        if self.mock_mode:
            # Temporary mock failure rule for testing:
            # Any loginid containing "fail" will simulate a failed creation.
            if "fail" in loginid.lower():
                return {
                    "success": False,
                    "loginid": loginid,
                    "payload": payload,
                    "system_response_code": "MOCK_500",
                    "error_code": "ERR_005",
                    "error_description": "Mock user creation failure"
                }

            return {
                "success": True,
                "loginid": loginid,
                "payload": payload,
                "system_response_code": "MOCK_201",
                "uuid": payload["uuid"]
            }

        raise NotImplementedError(
            "Real API integration is not enabled in this step. Keep MOCK_MODE = true for now."
        )

    def delete_user(self, loginid):
        if self.mock_mode:
            return {
                "success": True,
                "loginid": loginid,
                "system_response_code": "MOCK_DELETE_200"
            }

        raise NotImplementedError(
            "Real delete API integration is not enabled in this step. Keep MOCK_MODE = true for now."
        )