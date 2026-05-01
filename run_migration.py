from src.config_loader import ConfigLoader


def main():
    config_loader = ConfigLoader()
    config_loader.load_config()

    paths = config_loader.get_paths()
    target = config_loader.get_target_config()
    batch_config = config_loader.get_batch_config()

    print("Configuration loaded successfully.")
    print("Paths:", paths)
    print("Target:", target)
    print("Batch Config:", batch_config)


if __name__ == "__main__":
    main()