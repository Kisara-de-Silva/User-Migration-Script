import logging
import os


def setup_batch_logger(log_dir, batch_file_name):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    batch_base_name = os.path.splitext(batch_file_name)[0]
    log_file_path = os.path.join(log_dir, f"{batch_base_name}.log")

    logger_name = f"migration_logger_{batch_base_name}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Prevent duplicate log entries when script is run multiple times
    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger