import os
import sys
import tempfile
import logging
from typing import Tuple

# --- CONFIGURATION IMPORT ---
from config.bot_config import BotConfig

# --- LOGGER SETUP ---
utils_logger = logging.getLogger("utils")
utils_logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
utils_logger.addHandler(console_handler)
# --- END OF EXPLICIT SETUP ---


def validate_video_file(file_path: str) -> Tuple[bool, str]:
    """Validate if the file is a supported video format"""
    if not os.path.exists(file_path):
        return False, "File does not exist"

    file_size = os.path.getsize(file_path)
    # --- USE VALUE FROM CONFIGURATION ---
    max_size = BotConfig.MAX_VIDEO_SIZE

    if file_size > max_size:
        # --- USE VALUE FROM CONFIGURATION IN ERROR MESSAGE ---
        return False, f"File size exceeds {BotConfig.MAX_VIDEO_SIZE_MB}MB limit"

    file_ext = os.path.splitext(file_path)[1][1:].lower()
    supported_formats = ["mp4", "avi", "mov", "mkv"]

    if file_ext not in supported_formats:
        return (
            False,
            f"Unsupported file format. Supported formats: {', '.join(supported_formats)}",
        )

    return True, "Valid video file"


def cleanup_temp_file(file_path: str):
    """Remove temporary file with improved logging"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            utils_logger.info(f"Successfully removed temporary file: {file_path}")
        else:
            utils_logger.warning(f"Attempted to remove non-existent file: {file_path}")
    except Exception as e:
        utils_logger.error(f"Error removing temporary file {file_path}: {e}")


def create_temp_file(content: bytes, suffix: str = ".mp4") -> str:
    """Create a temporary file with the given content"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(content)
        return temp_file.name


