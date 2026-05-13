import configparser
import os


class ConfigLoader:
    def __init__(self, config_path="config.ini"):
        self.config_path = config_path
        self.config = configparser.ConfigParser()

    def load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        self.config.read(self.config_path)
        return self.config

    def get_paths(self):
        return {
            "source_dir": self.config["PATHS"]["SOURCE_DIR"],
            "destination_dir": self.config["PATHS"]["DESTINATION_DIR"],
            "log_dir": self.config["PATHS"]["LOG_DIR"],
            "tracker_file": self.config["PATHS"]["TRACKER_FILE"],
        }

    def get_target_config(self):
        protocol = self.config["TARGET"]["TARGET_PROTOCOL"]
        host = self.config["TARGET"]["TARGET_HOST"]
        port = self.config["TARGET"].get("TARGET_PORT", "").strip()

        if port:
            base_url = f"{protocol}://{host}:{port}"
        else:
            base_url = f"{protocol}://{host}"

        return {
            "target_host": host,
            "base_url": base_url,
            "create_user_url": base_url + self.config["TARGET"]["CREATE_USER_ENDPOINT"],
            "delete_user_url": base_url + self.config["TARGET"]["DELETE_USER_ENDPOINT"],
        }

    def get_batch_config(self):
        return {
            "batch_prefix": self.config["BATCH"]["BATCH_PREFIX"],
            "batch_extension": self.config["BATCH"]["BATCH_EXTENSION"],
        }
        
    def get_validation_config(self):
        expected_headers = self.config["VALIDATION"].get("EXPECTED_HEADERS", "")
        mandatory_fields = self.config["VALIDATION"]["MANDATORY_FIELDS"]
        true_values = self.config["VALIDATION"]["TRUE_VALUES"]
        false_values = self.config["VALIDATION"]["FALSE_VALUES"]

        return {
            "expected_headers": [
                header.strip() for header in expected_headers.split(",") 
                if header.strip()
            ],
            "mandatory_fields": [
                field.strip() for field in mandatory_fields.split(",")
                if field.strip()
            ],
            "true_values": [
                value.strip().lower() for value in true_values.split(",")
                if value.strip()
            ],
            "false_values": [
                value.strip().lower() for value in false_values.split(",")
                if value.strip()
            ],
        }
    
    def get_execution_config(self):
        mock_mode = self.config.getboolean("EXECUTION", "MOCK_MODE", fallback=True)

        return {
            "mock_mode": mock_mode
        }
    
    def get_output_config(self):
        output_fields = self.config["OUTPUT"]["OUTPUT_FIELDS"]

        return {
            "output_fields": [
                field.strip() for field in output_fields.split(",")
                if field.strip()
            ]
        }
    
    def get_scim_payload_config(self):
        return {
            "native_password": self.config["SCIM_PAYLOAD"].get("NATIVE_PASSWORD", "admin"),
            "preferred_language": self.config["SCIM_PAYLOAD"].get("PREFERRED_LANGUAGE", "SG"),
            "created_by": self.config["SCIM_PAYLOAD"].get("CREATED_BY", "migrationScript"),
            "mfa_config": self.config["SCIM_PAYLOAD"].get(
                "MFA_CONFIG",
                "{\"SMS\": true, \"EMAIL\": true, \"SOFT_TOKEN\": false, \"FIDO\": false}"
            )
        }
    
    def get_auth_config(self):
        return {
            "auth_type": self.config["AUTH"].get("AUTH_TYPE", "BASIC"),
            "username": self.config["AUTH"].get("USERNAME", ""),
            "password": self.config["AUTH"].get("PASSWORD", "")
        }

    def get_http_config(self):
        return {
            "request_timeout_seconds": self.config.getint(
                "HTTP",
                "REQUEST_TIMEOUT_SECONDS",
                fallback=30
            ),
            "verify_ssl": self.config.getboolean(
                "HTTP",
                "VERIFY_SSL",
                fallback=True
            )
        }
    
    def get_duplicate_check_config(self):
        return {
            "enabled": self.config.getboolean(
                "DUPLICATE_CHECK",
                "ENABLED",
                fallback=True
            ),
            "attribute": self.config["DUPLICATE_CHECK"].get(
                "ATTRIBUTE",
                "CombankDetails.unifiedUsername"
            ),
            "use_quotes": self.config.getboolean(
                "DUPLICATE_CHECK",
                "USE_QUOTES",
                fallback=True
            )
        }
    
