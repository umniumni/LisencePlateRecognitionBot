import os
from dotenv import load_dotenv

load_dotenv()


class BotConfig:
    TOKEN = os.getenv("BOT_TOKEN")
    DETECTION_MODEL_PATH = os.getenv("DETECTION_MODEL_PATH", "weights/detection.pt")
    RECOGNITION_MODEL_PATH = os.getenv(
        "RECOGNITION_MODEL_PATH", "weights/recognition.pt"
    )
    DEFAULT_ACCURACY = int(os.getenv("DEFAULT_ACCURACY", 75))
    STORAGE_FILE_PATH = os.getenv("STORAGE_FILE_PATH", "data/license_plates.json")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Bot settings
    MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "20"))
    MAX_VIDEO_SIZE = MAX_VIDEO_SIZE_MB * 1024 * 1024
    SUPPORTED_VIDEO_FORMATS = ["mp4", "avi", "mov", "mkv"]

    # Detection settings
    CONFIDENCE_THRESHOLD = 0.75
    IOU_THRESHOLD = 0.4

    # Possible values: 'off', '90', '180', '270'
    CAMERA_ROTATION = os.getenv("CAMERA_ROTATION", "off")

    # Time in seconds that a license plate must be absent for the session to be considered complete.
    CAMERA_SESSION_TIMEOUT_SECONDS = int(
        os.getenv("CAMERA_SESSION_TIMEOUT_SECONDS", "5")
    )

    # Default camera processing duration in seconds
    DEFAULT_CAMERA_DURATION_SECONDS = int(
        os.getenv("DEFAULT_CAMERA_DURATION_SECONDS", "60")
    )

    # Minimum confidence threshold for cameras (as a percentage of the standard)
    CAMERA_CONFIDENCE_FACTOR = float(os.getenv("CAMERA_CONFIDENCE_FACTOR", "0.7"))

    # Time in seconds after which the car is considered to have left (for cameras)
    CAMERA_PLATE_ABSENT_SECONDS = int(os.getenv("CAMERA_PLATE_ABSENT_SECONDS", "3"))

