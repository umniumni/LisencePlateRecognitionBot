START_MESSAGE = "🚗 Welcome to License Plate Recognition Bot! 🚗\n\nThis bot can detect license plates from videos or camera streams.\n\nChoose an option below to get started:"
VIDEO_INSTRUCTION = "📹 Send me a video file with cars, and I'll detect the license plates.\n\nExample: Upload a video of cars on a road."
CAMERA_INSTRUCTION = "📷 Send me a <b>camera IP address in RTSP format</b>, and I'll connect to detect license plates in real-time.\n\n<b>Example:</b> rtsp://192.168.14.709:334/user=admin_password=_channel=2_stream=1.sdp\nor\nrtsp://192.168.12.200:8080/h201_okaw.sdp\n\nYou can also specify the duration in seconds by adding <b>?duration=N</b> to the URL, where N is the number of seconds.\n\n<b>Example:</b> rtsp://192.168.14.709:334/user=admin_password=_channel=2_stream=1.sdp?duration=120"
PROCESSING_VIDEO = "⏳ Processing your video... This may take a few minutes."
PROCESSING_CAMERA = "📡 Connecting to camera and detecting license plates..."
NO_PLATES_FOUND = "❌ No license plates detected in the video."
CAMERA_ERROR = "❌ Failed to connect to the camera. Please check the IP address and try again."
ACCURACY_UPDATED = "✅ Accuracy updated to {accuracy}%"
INVALID_ACCURACY = "❌ Invalid accuracy value. Please enter a number between 0 and 100."
RESET_SUCCESS = "✅ Counters have been reset successfully."
SEARCH_NOT_FOUND = "❌ License plate '{plate}' not found in the records."
SEARCH_FOUND = "✅ License plate '{plate}' found {count} time(s) in the records."
CONFIG_INSTRUCTION = "⚙️ Choose a configuration option to adjust:"
ACCURACY_INSTRUCTION = "🎯 Send me a number between 0 and 100 to set the detection accuracy.\n\nCurrent accuracy: {current_accuracy}%"

NO_PLATES_FOUND_WITH_SUGGESTIONS = """
❌ No license plates detected.

This could happen if:
• There were no cars with visible plates in the video.
• The camera angle or lighting made the plates difficult to recognize.
• The video orientation is incorrect.
• The confidence threshold is too high for the current conditions.

What you can try:
• Ensure the camera has a clear view of the license plates and a proper angle.
• If you recorded the video with a phone, check how you held it:
    • <b>Landscape (horizontal) mode*</b> usually requires no rotation.
    • <b>Portrait (vertical) mode*</b> often results in a video that needs to be rotated 90°.
• Use the '⚙️ Configuration' -> '🔄 Rotate Camera' menu to manually fix the video angle. Try the '90°' option if the video was shot vertically.
• Lower the detection accuracy in the '⚙️ Configuration' -> '🎯 Accuracy' menu. A lower value may detect more plates but might increase false positives.

<b>Check Advanced Settings:</b>
Sometimes, detection can be affected by the bot's configuration. You can check and adjust these in the '⚙️ Configuration' menu:
• <b>🎯 Accuracy:</b> If set too high, the bot might ignore slightly blurry or small plates. If too low, it might find false positives.
• <b>🖼️ Frame Skip:</b> If set too high, the bot might skip the exact frame where a license plate is most visible.
• <b>⏱️ Session Timeout:</b> If set too low, the same car might be counted multiple times. If too high, it might not be counted at all if its plate is briefly hidden.
• <b>⏱️ Camera Duration:</b> If set too low, the bot might not have enough time to detect all license plates. If too high, processing will take longer.
"""

# --- HELP MESSAGE ---
HELP_MESSAGE = """
<b>🤖 License Plate Recognition Bot - Help</b>

I can help you detect and count license plates from videos or live camera streams. Choose a command below to get started, or use the main menu buttons for more options.

<b>🔹 Main Commands:</b>
• <code>/start</code> - Show the main menu.
• <code>/status</code> - Show current bot status.
• <code>/stats</code> - Show recent detection stats.
• <code>/help</code> - Show this help message.

<b>🔹 Main Menu Options:</b>
• <b>📹 Video Detection</b>: Send me a video file, and I'll analyze it for license plates.
• <b>📷 Camera Detection</b>: Provide an RTSP camera stream link for real-time detection.
• <b>🔍 Search</b>: Search for a specific license plate in my detection history.
• <b>🔄 Reset Counters</b>: Clear all previously saved detection data.
• <b>⚙️ Configuration</b>: Adjust detection settings like accuracy, frame skip, session timeout, and camera duration.

<b>🔹 Configuration Options:</b>
• <b>🎯 Accuracy</b>: Set the confidence level for plate detection (0-100%).
• <b>🖼️ Frame Skip:</b>: Control how many frames to skip for faster processing.
• <b>⏱️ Session Timeout:</b>: Define how long to wait for a new plate before ending a car's counting session.
• <b>🔄 Rotate Camera</b>: Manually adjust the video rotation if the camera is positioned incorrectly.
• <b>⏱️ Camera Duration:</b>: Set how long to process the camera stream in seconds.

If you're stuck, just press the <b>🔙 Back</b> button to return to the previous menu.
"""

# --- MESSAGES FOR COMMANDS ---
STATUS_MESSAGE = """
📊 <b>Current Bot Status</b>

🎯 Accuracy: {accuracy}%
🖼️ Frame Skip: {frame_skip}
⏱️ Session Timeout: {session_timeout}
🔄 Camera Rotation: {rotation}
⏱️ Camera Duration: {camera_duration}s
🚗 Total Detections: {total_detections}
"""

STATS_MESSAGE = """
📈 <b>Recent Detection Stats</b>

Last {count} unique plates found:
{plates_list}
"""

UNKNOWN_COMMAND_MESSAGE = "Sorry, I don't understand you. 🤷‍♂️\n\nPlease use the buttons below\n\nOr type <code>/help</code> to see available commands. 🙏"

FRAME_SKIP_INSTRUCTION = """
🖼️ <b>Frame Skip</b>

This setting controls how many frames the bot skips while analyzing a video.

*   <b>Lower value (e.g., 1-3):</b> Analyzes more frames. <b>Higher accuracy</b>, especially for fast-moving cars. <b>Slower processing.</b>
*   <b>Higher value (e.g., 10-20):</b> Skips more frames. <b>Faster processing</b>, but might miss fast cars.

<b>Recommendations:</b>
*   For videos with fast-changing cars: Set to <b>1-3</b>.
*   For slow traffic or long videos: Set to <b>10-15</b>.

Current value: {current_value}

Please send me a new value (a positive integer) to update this setting.
"""

SESSION_TIMEOUT_INSTRUCTION = """
⏱️ <b>Session Timeout</b>

This setting defines how long the bot waits for a new license plate before considering a car "gone" and ending its counting session. The value is in <i>analyzed frames</i>.

*   <b>Lower value (e.g., 2-5):</b> Separates cars quickly. Good for traffic where cars follow each other closely.
*   <b>Higher value (e.g., 10-20):</b> Waits longer. Useful if a single car's license plate might be briefly obscured.

<b>Recommendations:</b>
*   For videos with fast-changing cars: Set to <b>2-5</b>.
*   For rare/slow cars: Set to <b>10-15</b>.

Current value: {current_value}

Please send me a new value (a positive integer) to update this setting.
"""

CAMERA_DURATION_INSTRUCTION = """
⏱️ <b>Camera Duration</b>

This setting defines how long the bot will process the camera stream in seconds.

*   <b>Lower value (e.g., 30-60):</b> Faster processing, but might miss some license plates.
*   <b>Higher value (e.g., 120-300):</b> More thorough processing, but takes longer.

<b>Recommendations:</b>
*   For quick testing: Set to <b>30-60</b>.
*   For thorough detection: Set to <b>120-300</b>.

Current value: {current_value}

Please send me a new value (a positive integer in seconds) to update this setting.
"""

INVALID_INTEGER = "❌ Invalid value. Please enter a positive integer."
SETTINGS_UPDATED = "✅ Settings updated! Returning to configuration menu."


