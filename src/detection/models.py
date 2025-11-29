import logging
import re
import threading
import time
import cv2
import os
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class LicensePlateDetector:
    def __init__(self):
        # Map character classes to actual characters
        self.character_map = [
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
        ]

        # Initially all models and libraries are not loaded
        self.license_plate_model = None
        self.character_model = None
        self.cv2 = None
        self.np = None

        # Confidence threshold that will be controlled by the "Accuracy" setting in the bot
        self.confidence_threshold = 0.75
        self.iou_threshold = 0.4

        # Regular expression for validating Uzbek license plates
        self.plate_regex = re.compile(
            r"^(\d{2}[A-Za-z]\d{3}[A-Za-z]{2}|"  # Old format: 01A123BC
            r"[A-Za-z]\d{4}[A-Za-z]{2}|"  # New private/diplomatic: A1234BC
            r"[A-Za-z]{2}\d{4}[A-Za-z]{2}|"  # State: AA1234BB
            r"[A-Za-z]{2}\d{5})$"  # Temporary: TP12345
        )

        # --- CONFIGURABLE PARAMETERS ---
        # How many frames to skip to speed up processing
        self.process_every_n_frames = 1  # Decrease value to process more frames
        # How many frames must pass without a license plate for the session to end
        self.session_timeout_frames = 2

        # --- CAMERA ROTATION SETTINGS ---
        self.rotation_setting = "off"

        # Flags for lazy loading of models
        self._models_loaded = False
        self._load_lock = threading.Lock()
        self._is_loading = False

        # Counter for saving debug frames
        self.debug_frame_counter = 0

    def _is_valid_plate(self, plate_text: str) -> bool:
        """Validates if the license plate matches the specified format."""
        is_valid = bool(self.plate_regex.fullmatch(plate_text))
        if not is_valid and plate_text:  # Check that the string is not empty
            # INFO log level to see rejected plates
            logger.warning(f"Detected plate '{plate_text}' was REJECTED - does not match required format.")
        return is_valid

    def start_background_loading(self):
        """Starts loading models in a background thread."""
        with self._load_lock:
            if self._is_loading or self._models_loaded:
                return

            self._is_loading = True
            logger.info("Starting background model loading...")
            thread = threading.Thread(target=self._sync_load_dependencies, daemon=True)
            thread.start()

    def _sync_load_dependencies(self):
        """Synchronously loads all dependencies and models."""
        try:
            import cv2
            import numpy as np
            from ultralytics import YOLO
            from config.bot_config import BotConfig

            self.cv2 = cv2
            self.np = np
            self.license_plate_model = YOLO(BotConfig.DETECTION_MODEL_PATH)
            self.character_model = YOLO(BotConfig.RECOGNITION_MODEL_PATH)
            # Set thresholds from config on first load
            self.confidence_threshold = BotConfig.CONFIDENCE_THRESHOLD
            self.iou_threshold = BotConfig.IOU_THRESHOLD

            self._models_loaded = True
            logger.info("Dependencies and models loaded successfully in background.")
        except Exception as e:
            logger.error(f"Error during background model loading: {e}")
        finally:
            self._is_loading = False

    def _load_dependencies(self):
        """Ensures the models are loaded, loading them if necessary."""
        if self._models_loaded:
            return

        while self._is_loading:
            time.sleep(0.1)

        if not self._models_loaded:
            logger.info(
                "Background warm-up failed or not started, loading models on demand..."
            )
            self._sync_load_dependencies()

    # --- METHODS FOR CONTROLLING PARAMETERS FROM THE BOT ---

    def update_accuracy(self, accuracy_percent: int):
        """Updates the confidence threshold based on the value from the bot (0-100)."""
        # The Accuracy parameter from the bot directly affects the confidence_threshold
        self.confidence_threshold = accuracy_percent / 100.0
        logger.info(
            f"Detection accuracy (confidence_threshold) updated to {accuracy_percent}% ({self.confidence_threshold})"
        )

    def update_frame_skip(self, frame_skip: int):
        if frame_skip < 1:
            frame_skip = 1
        self.process_every_n_frames = frame_skip
        logger.info(f"Frame skip updated to {frame_skip}")

    def update_session_timeout(self, timeout_frames: int):
        if timeout_frames < 1:
            timeout_frames = 1
        self.session_timeout_frames = timeout_frames
        logger.info(f"Session timeout updated to {timeout_frames}")

    def get_frame_skip(self) -> int:
        return self.process_every_n_frames

    def get_session_timeout(self) -> int:
        return self.session_timeout_frames

    # --- MAIN DETECTION METHODS ---

    def detect_from_video(self, video_path: str) -> Dict[str, int]:
        """
        Detects and counts license plates in a video file.
        The counting logic is based on sessions: one car = one session.
        """
        self._load_dependencies()

        logger.info(f"Opening video file: {video_path}")
        cap = self.cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video file: {video_path}")
            return {}

        final_counts = {}
        current_session_plates = []
        frames_without_plate = 0
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % self.process_every_n_frames != 0:
                continue

            plates_in_frame = self._detect_plates_in_frame(frame)

            if plates_in_frame:
                frames_without_plate = 0
                current_session_plates.extend(plates_in_frame)
            else:
                frames_without_plate += 1

            # If a license plate is not visible for the specified time, the session ends
            if (
                frames_without_plate >= self.session_timeout_frames
                and current_session_plates
            ):
                # Use the approach to count all unique plates in a session
                # Instead of taking only the most frequent plate, we count all unique plates
                unique_plates_in_session = list(set(current_session_plates))
                
                for plate in unique_plates_in_session:
                    final_counts[plate] = final_counts.get(plate, 0) + 1
                
                logger.info(
                    f"Video session ended. Unique plates in session: {unique_plates_in_session}. Updated counts: {final_counts}"
                )
                current_session_plates = []

        # Process the last session if the video ended on a license plate
        if current_session_plates:
            # Count all unique plates in the last session
            unique_plates_in_session = list(set(current_session_plates))
            
            for plate in unique_plates_in_session:
                final_counts[plate] = final_counts.get(plate, 0) + 1
            
            logger.info(
                f"Final video session. Unique plates in session: {unique_plates_in_session}. Updated counts: {final_counts}"
            )

        cap.release()
        logger.info(
            f"Video processing finished. Detected unique plates: {final_counts}"
        )
        return final_counts

    def detect_from_camera(
        self,
        camera_url: str,
        rotation_setting: str,
        duration_seconds: int = 30,
    ) -> Dict[str, int]:
        """
        Detects and counts license plates from an RTSP stream, 
        using the same logic as video processing for consistency.
        """
        self._load_dependencies()

        logger.info(
            f"[DETECT_FROM_CAMERA] Starting processing with rotation setting: '{rotation_setting}' for {duration_seconds}s"
        )

        cap = self.cv2.VideoCapture(camera_url)
        if not cap.isOpened():
            logger.error(f"Could not open camera stream: {camera_url}")
            return {}

        # Set a more correct FPS value
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize delay
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 100:  # Check for incorrect values
            fps = 30  # Default value if unable to get correct FPS

        total_frames = int(fps * duration_seconds)
        logger.info(
            f"Starting camera processing for {duration_seconds}s. Estimated frames: {total_frames} (at {fps} FPS)."
        )

        # Logic for tracking multiple license plates
        final_counts = {}
        active_sessions = {}  # Dictionary for tracking active sessions for each license plate
        frame_count = 0
        debug_dir = "debug_frames"
        os.makedirs(debug_dir, exist_ok=True)  # Create folder for debug frames

        while cap.isOpened() and frame_count < total_frames:
            ret, frame = cap.read()
            if not ret:
                break

            # --- FRAME ROTATION LOGIC ---
            if rotation_setting == "90":
                frame = self.cv2.rotate(frame, self.cv2.ROTATE_90_CLOCKWISE)
            elif rotation_setting == "180":
                frame = self.cv2.rotate(frame, self.cv2.ROTATE_180)
            elif rotation_setting == "270":
                frame = self.cv2.rotate(frame, self.cv2.ROTATE_90_COUNTERCLOCKWISE)
            # 'off' means no rotation

            frame_count += 1
            if frame_count % self.process_every_n_frames != 0:
                continue

            if frame_count % 50 == 0:
                logger.info(f"Processed camera frame {frame_count}/{total_frames}")

            plates_in_frame = self._detect_plates_in_frame(frame)

            # Save debug frames every 100 frames or when license plates are detected
            if frame_count % 100 == 0 or plates_in_frame:
                debug_frame_path = os.path.join(
                    debug_dir, f"debug_frame_{frame_count}.jpg"
                )
                self.cv2.imwrite(debug_frame_path, frame)
                logger.debug(f"Saved debug frame to {debug_frame_path}")

            # Update active sessions for each detected license plate
            for plate in plates_in_frame:
                if plate not in active_sessions:
                    active_sessions[plate] = 0
                active_sessions[plate] = (
                    0  # Reset the frame counter without detection for this license plate
                )

            # Decrease the counter for license plates that were not detected in this frame
            plates_to_remove = []
            for plate, counter in active_sessions.items():
                if plate not in plates_in_frame:
                    active_sessions[plate] += 1
                    if active_sessions[plate] >= self.session_timeout_frames:
                        # Session for this license plate is finished
                        final_counts[plate] = final_counts.get(plate, 0) + 1
                        logger.info(
                            f"Camera session for plate '{plate}' ended. New total count: {final_counts[plate]}"
                        )
                        plates_to_remove.append(plate)

            # Remove completed sessions
            for plate in plates_to_remove:
                del active_sessions[plate]

            # Add detailed logging
            if plates_in_frame:
                logger.info(
                    f"Detected plates in frame {frame_count}: {plates_in_frame}"
                )
                logger.info(f"Active sessions: {list(active_sessions.keys())}")

        # Complete all remaining active sessions
        for plate in active_sessions:
            final_counts[plate] = final_counts.get(plate, 0) + 1
            logger.info(
                f"Final camera session for plate '{plate}'. New total count: {final_counts[plate]}"
            )

        cap.release()
        logger.info(
            f"Camera processing finished. Detected unique plates: {final_counts}"
        )
        logger.info(f"Debug frames saved to {debug_dir} directory")
        return final_counts

    def _detect_plates_in_frame(self, frame) -> List[str]:
        """
        Detects and recognizes ALL license plates in a single frame.
        Returns a list with the text of all valid plates.
        """
        self._load_dependencies()

        detected_plates_text = []

        # Use confidence_threshold that is controlled by the "Accuracy" setting
        # Reduce the threshold to detect more license plates
        adjusted_confidence = max(0.1, self.confidence_threshold * 0.7)
        logger.debug(
            f"Using adjusted confidence threshold: {adjusted_confidence} (original: {self.confidence_threshold})"
        )

        license_plates = self.license_plate_model(
            frame, conf=adjusted_confidence, iou=self.iou_threshold
        )

        if not license_plates[0].boxes:
            return []

        # INFO log level for visibility
        logger.info(f"Detected {len(license_plates[0].boxes)} license plate regions in frame.")

        # Don't sort by confidence, but process ALL found boxes
        for i, plate in enumerate(license_plates[0].boxes):
            x1, y1, x2, y2 = map(int, plate.xyxy[0])
            confidence = float(plate.conf)
            # Log level changed to INFO
            logger.info(
                f"Processing plate region {i + 1}/{len(license_plates[0].boxes)} with confidence: {confidence:.2f}"
            )

            cropped_license_plate = frame[y1:y2, x1:x2]

            # Character recognition on the cropped license plate image
            characters = self.character_model(
                cropped_license_plate,
                conf=adjusted_confidence,  # Also use reduced confidence threshold
                iou=self.iou_threshold,
            )

            detected_characters = []
            for char in characters[0].boxes:
                x1_char, y1_char, x2_char, y2_char = map(int, char.xyxy[0])
                character_class = int(char.cls[0])
                detected_characters.append((character_class, x1_char))

            # Sort characters by X coordinate to restore the correct order
            detected_characters.sort(key=lambda char: char[1])
            license_text = "".join(
                [self.character_map[char[0]] for char in detected_characters]
            )

            # Check if the recognized text matches the license plate format
            if self._is_valid_plate(license_text):
                detected_plates_text.append(license_text)
                # INFO log level
                logger.info(
                    f"Detected valid plate: {license_text} with confidence: {confidence:.2f}"
                )
            # else:
            #     logger.debug(f"Detected invalid plate: {license_text}")

        # Final log on frame processing results
        logger.info(
            f"Finished processing frame. Valid plates found: {detected_plates_text}"
        )
        return detected_plates_text


