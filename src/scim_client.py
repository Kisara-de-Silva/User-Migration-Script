import base64
from urllib.parse import quote

import requests
from requests.exceptions import RequestException, Timeout


class SCIMClient:
    def __init__(
        self,
        create_user_url,
        delete_user_url,
        auth_type,
        username,
        password,
        timeout_seconds=30,
        verify_ssl=True
    ):
        self.create_user_url = create_user_url
        self.delete_user_url = delete_user_url
        self.auth_type = auth_type.upper()
        self.username = username
        self.password = password
        self.timeout_seconds = timeout_seconds
        self.verify_ssl = verify_ssl

    def get_auth(self):
        if self.auth_type == "BASIC":
            return (self.username, self.password)

        return None

    def get_headers(self):
        return {
            "Content-Type": "application/scim+json",
            "Accept": "application/scim+json"
        }

    def parse_response_body(self, response):
        try:
            return response.json()
        except ValueError:
            return {
                "raw_response": response.text
            }

    def create_user(self, api_payload):
        try:
            response = requests.post(
                self.create_user_url,
                json=api_payload,
                headers=self.get_headers(),
                auth=self.get_auth(),
                timeout=self.timeout_seconds,
                verify=self.verify_ssl
            )

            response_body = self.parse_response_body(response)

            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_body": response_body
                }

            if response.status_code == 409:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error_code": "ERR_004",
                    "error_description": f"Duplicate Login ID or SCIM conflict. Response: {response_body}",
                    "response_body": response_body
                }

            return {
                "success": False,
                "status_code": response.status_code,
                "error_code": "ERR_005",
                "error_description": f"SCIM create failed. HTTP {response.status_code}. Response: {response_body}",
                "response_body": response_body
            }

        except Timeout:
            return {
                "success": False,
                "status_code": "TIMEOUT",
                "error_code": "ERR_005",
                "error_description": "SCIM create request timed out",
                "response_body": None
            }

        except RequestException as exception:
            return {
                "success": False,
                "status_code": "REQUEST_ERROR",
                "error_code": "ERR_005",
                "error_description": f"SCIM create request failed: {str(exception)}",
                "response_body": None
            }

    def encode_uuid_for_delete(self, user_uuid):
        encoded_uuid = base64.b64encode(user_uuid.encode("utf-8")).decode("utf-8")
        return quote(encoded_uuid, safe="")

    def delete_user(self, user_uuid):
        encoded_uuid = self.encode_uuid_for_delete(user_uuid)
        delete_url = f"{self.delete_user_url}/{encoded_uuid}"

        try:
            response = requests.delete(
                delete_url,
                headers=self.get_headers(),
                auth=self.get_auth(),
                timeout=self.timeout_seconds,
                verify=self.verify_ssl
            )

            response_body = self.parse_response_body(response)

            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "delete_url": delete_url,
                    "response_body": response_body
                }

            return {
                "success": False,
                "status_code": response.status_code,
                "delete_url": delete_url,
                "error_code": "ERR_005",
                "error_description": f"SCIM delete failed. HTTP {response.status_code}. Response: {response_body}",
                "response_body": response_body
            }

        except Timeout:
            return {
                "success": False,
                "status_code": "TIMEOUT",
                "delete_url": delete_url,
                "error_code": "ERR_005",
                "error_description": "SCIM delete request timed out",
                "response_body": None
            }

        except RequestException as exception:
            return {
                "success": False,
                "status_code": "REQUEST_ERROR",
                "delete_url": delete_url,
                "error_code": "ERR_005",
                "error_description": f"SCIM delete request failed: {str(exception)}",
                "response_body": None
            }
        
    def check_duplicate_by_unified_username(
        self,
        loginid,
        attribute_name="CombankDetails.unifiedUsername",
        use_quotes=True
    ):
        if use_quotes:
            filter_expression = f'{attribute_name} eq "{loginid}"'
        else:
            filter_expression = f"{attribute_name} eq {loginid}"

        try:
            response = requests.get(
                self.create_user_url,
                params={"filter": filter_expression},
                headers=self.get_headers(),
                auth=self.get_auth(),
                timeout=self.timeout_seconds,
                verify=self.verify_ssl
            )

            response_body = self.parse_response_body(response)

            if 200 <= response.status_code < 300:
                total_results = response_body.get("totalResults")

                if total_results is not None:
                    try:
                        is_duplicate = int(total_results) > 0
                    except (ValueError, TypeError):
                        resources = response_body.get("Resources", [])
                        is_duplicate = len(resources) > 0
                else:
                    resources = response_body.get("Resources", [])
                    is_duplicate = len(resources) > 0

                return {
                    "check_success": True,
                    "is_duplicate": is_duplicate,
                    "status_code": response.status_code,
                    "request_url": response.url,
                    "response_body": response_body
                }

            return {
                "check_success": False,
                "is_duplicate": False,
                "status_code": response.status_code,
                "request_url": response.url,
                "error_code": "ERR_005",
                "error_description": f"Duplicate check failed. HTTP {response.status_code}. Response: {response_body}",
                "response_body": response_body
            }

        except Timeout:
            return {
                "check_success": False,
                "is_duplicate": False,
                "status_code": "TIMEOUT",
                "request_url": self.create_user_url,
                "error_code": "ERR_005",
                "error_description": "Duplicate check request timed out",
                "response_body": None
            }

        except RequestException as exception:
            return {
                "check_success": False,
                "is_duplicate": False,
                "status_code": "REQUEST_ERROR",
                "request_url": self.create_user_url,
                "error_code": "ERR_005",
                "error_description": f"Duplicate check request failed: {str(exception)}",
                "response_body": None
            }