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
        port = self.config["TARGET"]["TARGET_PORT"]

        base_url = f"{protocol}://{host}:{port}"

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
        mandatory_fields = self.config["VALIDATION"]["MANDATORY_FIELDS"]
        true_values = self.config["VALIDATION"]["TRUE_VALUES"]
        false_values = self.config["VALIDATION"]["FALSE_VALUES"]

        return {
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