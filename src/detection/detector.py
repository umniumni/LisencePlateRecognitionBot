import os
import tempfile
import logging
import asyncio
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from config.bot_config import BotConfig
from src.detection.models import LicensePlateDetector
from src.storage.storage_manager import StorageManager
from src.bot.utils import cleanup_temp_file

logger = logging.getLogger(__name__)


class PlateDetectionService:
    """Service class for handling license plate detection operations"""

    def __init__(self):
        self.detector = LicensePlateDetector()
        self.storage = StorageManager()
        # --- File for saving camera rotation settings ---
        self.rotation_config_path = "data/rotation_config.json"
        # --- File for saving camera duration settings ---
        self.camera_duration_config_path = "data/camera_duration_config.json"
        self._load_rotation_config()
        self._load_camera_duration_config()

    def _load_rotation_config(self):
        """Loads the rotation setting from the configuration file."""
        logger.info(
            f"Attempting to load rotation config from: {self.rotation_config_path}"
        )
        try:
            # Check if the file exists
            if not os.path.exists(self.rotation_config_path):
                logger.warning(
                    f"Config file not found at {self.rotation_config_path}. Will use default 'off'."
                )
                self.detector.rotation_setting = "off"
                return

            os.makedirs(os.path.dirname(self.rotation_config_path), exist_ok=True)
            with open(self.rotation_config_path, "r") as f:
                config = json.load(f)
                loaded_value = config.get("rotation", "off")
                self.detector.rotation_setting = loaded_value
                logger.info(
                    f"Successfully loaded rotation setting from config: '{self.detector.rotation_setting}'"
                )
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding JSON from {self.rotation_config_path}: {e}. Using default 'off'."
            )
            self.detector.rotation_setting = "off"
        except Exception as e:
            logger.error(f"Error loading rotation config: {e}. Using default 'off'.")
            self.detector.rotation_setting = "off"

    def _save_rotation_config(self):
        """Saves the rotation setting to the configuration file."""
        logger.info(
            f"Attempting to save rotation setting '{self.detector.rotation_setting}' to {self.rotation_config_path}"
        )
        try:
            os.makedirs(os.path.dirname(self.rotation_config_path), exist_ok=True)
            with open(self.rotation_config_path, "w") as f:
                json.dump({"rotation": self.detector.rotation_setting}, f, indent=2)
                logger.info(
                    f"Successfully saved rotation setting to config: '{self.detector.rotation_setting}'"
                )
        except Exception as e:
            logger.error(f"CRITICAL: Error saving rotation config: {e}")

    def _load_camera_duration_config(self):
        """Loads the camera duration setting from the configuration file."""
        logger.info(
            f"Attempting to load camera duration config from: {self.camera_duration_config_path}"
        )
        try:
            # Check if the file exists
            if not os.path.exists(self.camera_duration_config_path):
                logger.warning(
                    f"Config file not found at {self.camera_duration_config_path}. Will use default from BotConfig."
                )
                self.camera_duration = BotConfig.DEFAULT_CAMERA_DURATION_SECONDS
                return

            os.makedirs(
                os.path.dirname(self.camera_duration_config_path), exist_ok=True
            )
            with open(self.camera_duration_config_path, "r") as f:
                config = json.load(f)
                loaded_value = config.get(
                    "duration", BotConfig.DEFAULT_CAMERA_DURATION_SECONDS
                )
                self.camera_duration = loaded_value
                logger.info(
                    f"Successfully loaded camera duration setting from config: '{self.camera_duration}s'"
                )
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding JSON from {self.camera_duration_config_path}: {e}. Using default from BotConfig."
            )
            self.camera_duration = BotConfig.DEFAULT_CAMERA_DURATION_SECONDS
        except Exception as e:
            logger.error(
                f"Error loading camera duration config: {e}. Using default from BotConfig."
            )
            self.camera_duration = BotConfig.DEFAULT_CAMERA_DURATION_SECONDS

    def _save_camera_duration_config(self):
        """Saves the camera duration setting to the configuration file."""
        logger.info(
            f"Attempting to save camera duration setting '{self.camera_duration}s' to {self.camera_duration_config_path}"
        )
        try:
            os.makedirs(
                os.path.dirname(self.camera_duration_config_path), exist_ok=True
            )
            with open(self.camera_duration_config_path, "w") as f:
                json.dump({"duration": self.camera_duration}, f, indent=2)
                logger.info(
                    f"Successfully saved camera duration setting to config: '{self.camera_duration}s'"
                )
        except Exception as e:
            logger.error(f"CRITICAL: Error saving camera duration config: {e}")

    async def process_video_file(self, file_path: str) -> Dict:
        try:
            logger.info(f"Processing video file: {file_path}")
            detected_counts = await asyncio.to_thread(
                self.detector.detect_from_video, file_path
            )

            if not detected_counts:
                return {
                    "success": True,
                    "plates": {},
                    "message": "No license plates detected in the video",
                }

            for plate, count in detected_counts.items():
                for _ in range(count):
                    self.storage.add_plate(plate)

            return {
                "success": True,
                "plates": detected_counts,
                "message": f"Detected {len(detected_counts)} unique license plates",
            }

        except Exception as e:
            logger.error(f"Error processing video file: {str(e)}")
            return {
                "success": False,
                "plates": {},
                "message": f"Error processing video: {str(e)}",
            }
        finally:
            cleanup_temp_file(file_path)

    async def process_camera_stream(
        self, camera_url: str, duration_seconds: Optional[int] = None
    ) -> Dict:
        try:
            logger.info(f"Processing camera stream: {camera_url}")

            # Use the value from the configuration if not specified otherwise
            if duration_seconds is None:
                duration_seconds = self.camera_duration

            rotation_setting = self.detector.rotation_setting
            logger.info(f"Using rotation setting: {rotation_setting}")
            logger.info(f"Using duration: {duration_seconds}s")

            import cv2

            cap = cv2.VideoCapture(camera_url)
            if not cap.isOpened():
                return {
                    "success": False,
                    "plates": {},
                    "message": "Failed to connect to camera. Please check the URL and try again.",
                }
            cap.release()

            detected_counts = await asyncio.to_thread(
                self.detector.detect_from_camera,
                camera_url,
                rotation_setting=rotation_setting,
                duration_seconds=duration_seconds,
            )

            if not detected_counts:
                return {
                    "success": True,
                    "plates": {},
                    "message": "No license plates detected in the camera stream",
                }

            for plate, count in detected_counts.items():
                for _ in range(count):
                    self.storage.add_plate(plate)

            return {
                "success": True,
                "plates": detected_counts,
                "message": f"Detected {len(detected_counts)} unique license plates from camera",
            }

        except Exception as e:
            logger.error(f"Error processing camera stream: {str(e)}")
            return {
                "success": False,
                "plates": {},
                "message": f"Error connecting to camera: {str(e)}",
            }

    def search_license_plate(self, plate_number: str) -> Dict:
        try:
            found, count = self.storage.search_plate(plate_number.upper())

            if found:
                return {
                    "success": True,
                    "found": True,
                    "plate": plate_number.upper(),
                    "count": count,
                    "message": f"License plate {plate_number} found {count} time(s)",
                }
            else:
                return {
                    "success": True,
                    "found": False,
                    "plate": plate_number.upper(),
                    "count": 0,
                    "message": f"License plate {plate_number} not found in records",
                }

        except Exception as e:
            logger.error(f"Error searching license plate: {str(e)}")
            return {
                "success": False,
                "found": False,
                "plate": plate_number,
                "count": 0,
                "message": f"Error searching license plate: {str(e)}",
            }

    def get_all_plates(self) -> Dict:
        try:
            plates = self.storage.get_all_plates()

            return {
                "success": True,
                "plates": plates,
                "total_plates": len(plates),
                "total_detections": sum(plates.values()),
                "message": f"Found {len(plates)} unique license plates with {sum(plates.values())} total detections",
            }

        except Exception as e:
            logger.error(f"Error getting all plates: {str(e)}")
            return {
                "success": False,
                "plates": {},
                "total_plates": 0,
                "total_detections": 0,
                "message": f"Error retrieving license plates: {str(e)}",
            }

    def reset_counters(self) -> Dict:
        try:
            self.storage.reset_all()

            return {
                "success": True,
                "message": "All license plate counters have been reset successfully",
            }

        except Exception as e:
            logger.error(f"Error resetting counters: {str(e)}")
            return {"success": False, "message": f"Error resetting counters: {str(e)}"}

    def update_accuracy(self, accuracy_percent: int) -> Dict:
        try:
            if not 0 <= accuracy_percent <= 100:
                return {
                    "success": False,
                    "message": "Invalid accuracy value. Please enter a number between 0 and 100.",
                }

            self.detector.update_accuracy(accuracy_percent)

            return {
                "success": True,
                "accuracy": accuracy_percent,
                "message": f"Detection accuracy updated to {accuracy_percent}%",
            }

        except Exception as e:
            logger.error(f"Error updating accuracy: {str(e)}")
            return {"success": False, "message": f"Error updating accuracy: {str(e)}"}

    def get_current_accuracy(self) -> Dict:
        try:
            current_accuracy = int(self.detector.confidence_threshold * 100)

            return {
                "success": True,
                "accuracy": current_accuracy,
                "message": f"Current detection accuracy is {current_accuracy}%",
            }

        except Exception as e:
            logger.error(f"Error getting current accuracy: {str(e)}")
            return {
                "success": False,
                "accuracy": 0,
                "message": f"Error getting current accuracy: {str(e)}",
            }

    def validate_camera_url(self, url: str) -> Dict:
        try:
            if not url.strip():
                return {"success": False, "message": "Camera URL cannot be empty"}

            if not url.startswith("rtsp://"):
                return {
                    "success": False,
                    "message": "Invalid camera URL. Please provide a valid RTSP URL starting with 'rtsp://'",
                }

            import cv2

            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                return {
                    "success": False,
                    "message": "Failed to connect to camera. Please check the URL and network connection.",
                }
            cap.release()

            return {"success": True, "message": "Camera URL is valid"}

        except Exception as e:
            logger.error(f"Error validating camera URL: {str(e)}")
            return {
                "success": False,
                "message": f"Error validating camera URL: {str(e)}",
            }

    # --- WRAPPER METHODS ---
    def get_frame_skip(self) -> Dict:
        try:
            current_value = self.detector.get_frame_skip()
            return {
                "success": True,
                "value": current_value,
                "message": f"Current frame skip is {current_value}.",
            }
        except Exception as e:
            logger.error(f"Error getting frame skip: {str(e)}")
            return {"success": False, "message": f"Error getting frame skip: {str(e)}"}

    def update_frame_skip(self, frame_skip: int) -> Dict:
        try:
            if not isinstance(frame_skip, int) or frame_skip < 1:
                return {
                    "success": False,
                    "message": "Invalid value. Please enter a positive integer.",
                }

            self.detector.update_frame_skip(frame_skip)
            return {
                "success": True,
                "value": frame_skip,
                "message": f"Frame skip updated to {frame_skip}.",
            }
        except Exception as e:
            logger.error(f"Error updating frame skip: {str(e)}")
            return {"success": False, "message": f"Error updating frame skip: {str(e)}"}

    def get_session_timeout(self) -> Dict:
        try:
            current_value = self.detector.get_session_timeout()
            return {
                "success": True,
                "value": current_value,
                "message": f"Current session timeout is {current_value}.",
            }
        except Exception as e:
            logger.error(f"Error getting session timeout: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting session timeout: {str(e)}",
            }

    def update_session_timeout(self, timeout_frames: int) -> Dict:
        try:
            if not isinstance(timeout_frames, int) or timeout_frames < 1:
                return {
                    "success": False,
                    "message": "Invalid value. Please enter a positive integer.",
                }

            self.detector.update_session_timeout(timeout_frames)
            return {
                "success": True,
                "value": timeout_frames,
                "message": f"Session timeout updated to {timeout_frames}.",
            }
        except Exception as e:
            logger.error(f"Error updating session timeout: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating session timeout: {str(e)}",
            }

    # --- METHODS FOR CONTROLLING ROTATION ---
    def get_camera_rotation(self) -> str:
        """Gets the current camera rotation setting from the detector."""
        try:
            return self.detector.rotation_setting
        except Exception as e:
            logger.error(f"Error getting camera rotation setting: {str(e)}")
            return "off"  # Default value in case of error

    # --- METHOD FOR /status ---
    def get_rotation_status(self) -> Dict:
        """Gets the current rotation setting for the status command."""
        try:
            return {
                "success": True,
                "value": self.detector.rotation_setting,
                "message": f"Current camera rotation is {self.detector.rotation_setting}.",
            }
        except Exception as e:
            logger.error(f"Error getting rotation status: {str(e)}")
            return {
                "success": False,
                "value": "off",
                "message": f"Error getting rotation status: {str(e)}",
            }

    def update_camera_rotation(self, rotation: str) -> Dict:
        """
        Updates the camera rotation setting and saves it to a config file.
        """
        valid_rotations = ["off", "90", "180", "270"]
        if rotation not in valid_rotations:
            return {
                "success": False,
                "message": f"Invalid rotation value. Please choose from {valid_rotations}.",
            }

        # Update the setting in the detector
        self.detector.rotation_setting = rotation

        # Save the setting to the file
        self._save_rotation_config()

        return {
            "success": True,
            "value": rotation,
            "message": f"Camera rotation updated to {rotation}. This setting will be used for future camera detections.",
        }

    # --- METHODS FOR CONTROLLING CAMERA DURATION ---
    def get_camera_duration(self) -> Dict:
        """Gets the current camera duration setting."""
        try:
            return {
                "success": True,
                "value": self.camera_duration,
                "message": f"Current camera duration is {self.camera_duration} seconds.",
            }
        except Exception as e:
            logger.error(f"Error getting camera duration: {str(e)}")
            return {
                "success": False,
                "value": BotConfig.DEFAULT_CAMERA_DURATION_SECONDS,
                "message": f"Error getting camera duration: {str(e)}",
            }

    def update_camera_duration(self, duration_seconds: int) -> Dict:
        """
        Updates the camera duration setting and saves it to a config file.
        """
        if not isinstance(duration_seconds, int) or duration_seconds < 10:
            return {
                "success": False,
                "message": "Invalid duration value. Please enter a positive integer (at least 10 seconds).",
            }

        # Update the setting
        self.camera_duration = duration_seconds

        # Save the setting to the file
        self._save_camera_duration_config()

        return {
            "success": True,
            "value": duration_seconds,
            "message": f"Camera duration updated to {duration_seconds} seconds. This setting will be used for future camera detections.",
        }




