import os
import tempfile
import logging
from typing import Dict, List
from urllib.parse import urlparse, parse_qs

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, ChatMemberUpdatedFilter, MEMBER
from aiogram.types import ChatMemberUpdated
import asyncio

# --- CONFIGURATION IMPORT ---
from config.bot_config import BotConfig
from config.messages import (
    START_MESSAGE,
    VIDEO_INSTRUCTION,
    CAMERA_INSTRUCTION,
    PROCESSING_VIDEO,
    PROCESSING_CAMERA,
    NO_PLATES_FOUND,
    NO_PLATES_FOUND_WITH_SUGGESTIONS,
    CAMERA_ERROR,
    ACCURACY_UPDATED,
    INVALID_ACCURACY,
    RESET_SUCCESS,
    SEARCH_NOT_FOUND,
    SEARCH_FOUND,
    CONFIG_INSTRUCTION,
    ACCURACY_INSTRUCTION,
    FRAME_SKIP_INSTRUCTION,
    SESSION_TIMEOUT_INSTRUCTION,
    CAMERA_DURATION_INSTRUCTION,
    INVALID_INTEGER,
    SETTINGS_UPDATED,
    HELP_MESSAGE,
    UNKNOWN_COMMAND_MESSAGE,
    STATUS_MESSAGE,
    STATS_MESSAGE,
)
from config.buttons import (
    START_BUTTON,
    VIDEO_BUTTON,
    CAMERA_BUTTON,
    RESET_BUTTON,
    SEARCH_BUTTON,
    CONFIG_BUTTON,
    ACCURACY_BUTTON,
    BACK_BUTTON,
    FRAME_SKIP_BUTTON,
    SESSION_TIMEOUT_BUTTON,
    CAMERA_ROTATION_BUTTON,
    CAMERA_DURATION_BUTTON,
)
from src.detection.detector import PlateDetectionService
from src.bot.utils import validate_video_file, cleanup_temp_file, create_temp_file

from src.bot.keyboards import (
    get_start_keyboard,
    get_back_keyboard,
    get_config_keyboard,
    get_help_inline_keyboard,
    get_rotation_inline_keyboard,
)


# Define states for the FSM
class BotStates(StatesGroup):
    waiting_for_video = State()
    waiting_for_camera_url = State()
    waiting_for_search_query = State()
    waiting_for_accuracy_value = State()
    waiting_for_frame_skip_value = State()
    waiting_for_session_timeout_value = State()
    waiting_for_camera_duration_value = State()


# Create router
router = Router()

# Initialize detection service
detection_service = PlateDetectionService()

logger = logging.getLogger(__name__)


async def _process_start_command(chat_id: int, bot: Bot, state: FSMContext):
    """Core logic for the /start command"""
    await state.clear()
    await bot.send_message(chat_id, START_MESSAGE, reply_markup=get_start_keyboard())
    if not detection_service.detector._models_loaded:
        logger.info("Initiating background model warm-up after /start command.")
        detection_service.detector.start_background_loading()


async def _process_help_command(chat_id: int, bot: Bot):
    """Core logic for the /help command"""
    await bot.send_message(
        chat_id, HELP_MESSAGE, reply_markup=get_help_inline_keyboard()
    )


async def _process_status_command(chat_id: int, bot: Bot):
    """Core logic for the /status command"""
    accuracy_result = detection_service.get_current_accuracy()
    frame_skip_result = detection_service.get_frame_skip()
    timeout_result = detection_service.get_session_timeout()
    rotation_result = detection_service.get_rotation_status()
    duration_result = detection_service.get_camera_duration()
    plates_result = detection_service.get_all_plates()

    if all(
        res["success"]
        for res in [
            accuracy_result,
            frame_skip_result,
            timeout_result,
            rotation_result,
            duration_result,
            plates_result,
        ]
    ):
        message_text = STATUS_MESSAGE.format(
            accuracy=accuracy_result["accuracy"],
            frame_skip=frame_skip_result["value"],
            session_timeout=timeout_result["value"],
            rotation=rotation_result["value"],
            camera_duration=duration_result["value"],
            total_detections=plates_result["total_detections"],
        )

        await bot.send_message(
            chat_id,
            message_text,
            reply_markup=get_start_keyboard(),
        )
    else:
        await bot.send_message(
            chat_id,
            "❌ Could not retrieve some status information.",
            reply_markup=get_start_keyboard(),
        )


async def _process_stats_command(chat_id: int, bot: Bot):
    """Core logic for the /stats command"""
    plates_result = detection_service.get_all_plates()
    if plates_result["success"] and plates_result["plates"]:
        plates = plates_result["plates"]
        last_5_plates = list(plates.items())[-5:]
        plates_list = "\n".join(
            [f"• {plate}: {count} time(s)" for plate, count in last_5_plates]
        )
        await bot.send_message(
            chat_id,
            STATS_MESSAGE.format(count=len(last_5_plates), plates_list=plates_list),
            reply_markup=get_start_keyboard(),
        )
    else:
        await bot.send_message(
            chat_id,
            "📈 No license plates have been detected yet.",
            reply_markup=get_start_keyboard(),
        )


# --- COMMAND AND EVENT HANDLERS ---
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def bot_welcome(event: ChatMemberUpdated):
    await _process_help_command(event.chat.id, event.bot)

@router.message(Command("start"))
@router.message(F.text == START_BUTTON)
async def start_command(message: types.Message, state: FSMContext):
    await _process_start_command(message.chat.id, message.bot, state)


@router.message(Command("help"))
async def help_command(message: types.Message):
    await _process_help_command(message.chat.id, message.bot)


@router.message(Command("status"))
async def status_command(message: types.Message):
    await _process_status_command(message.chat.id, message.bot)


@router.message(Command("stats"))
async def stats_command(message: types.Message):
    await _process_stats_command(message.chat.id, message.bot)


@router.callback_query(F.data.startswith("cmd_"))
async def handle_command_callbacks(callback: types.CallbackQuery, state: FSMContext):
    """Handles clicks on inline buttons in the help message"""
    command = callback.data.split("_")[1]
    await callback.answer()

    if command == "start":
        await _process_start_command(callback.message.chat.id, callback.bot, state)
    elif command == "help":
        await callback.message.edit_text(
            HELP_MESSAGE, reply_markup=get_help_inline_keyboard()
        )
    elif command == "status":
        await _process_status_command(callback.message.chat.id, callback.bot)
    elif command == "stats":
        await _process_stats_command(callback.message.chat.id, callback.bot)


# --- OTHER HANDLERS ---
@router.message(F.text == VIDEO_BUTTON)
async def video_detection_command(message: types.Message, state: FSMContext):
    """Handle the video detection command"""
    await state.set_state(BotStates.waiting_for_video)
    await message.answer(VIDEO_INSTRUCTION, reply_markup=get_back_keyboard())


@router.message(F.text == CAMERA_BUTTON)
async def camera_detection_command(message: types.Message, state: FSMContext):
    """Handle the camera detection command"""
    await state.set_state(BotStates.waiting_for_camera_url)
    await message.answer(CAMERA_INSTRUCTION, reply_markup=get_back_keyboard())


@router.message(F.text == SEARCH_BUTTON)
async def search_command(message: types.Message, state: FSMContext):
    """Handle the search command"""
    await state.set_state(BotStates.waiting_for_search_query)
    await message.answer(
        "🔍 Enter the license plate number you want to search for:",
        reply_markup=get_back_keyboard(),
    )


@router.message(F.text == CONFIG_BUTTON)
async def config_command(message: types.Message, state: FSMContext):
    """Handle the configuration command"""
    await message.answer(CONFIG_INSTRUCTION, reply_markup=get_config_keyboard())


@router.message(F.text == ACCURACY_BUTTON)
async def accuracy_command(message: types.Message, state: FSMContext):
    """Handle the accuracy configuration command"""
    result = detection_service.get_current_accuracy()

    if result["success"]:
        await state.set_state(BotStates.waiting_for_accuracy_value)
        await message.answer(
            ACCURACY_INSTRUCTION.format(current_accuracy=result["accuracy"]),
            reply_markup=get_back_keyboard(),
        )
    else:
        await message.answer(
            f"❌ {result['message']}", reply_markup=get_config_keyboard()
        )


@router.message(F.text == CAMERA_ROTATION_BUTTON)
async def camera_rotation_command(message: types.Message):
    """Handle the camera rotation configuration command"""
    current_rotation = detection_service.get_camera_rotation()

    await message.answer(
        f"🔄 Choose the camera rotation angle.\n\nCurrent setting: <b>{current_rotation}</b>",
        reply_markup=get_rotation_inline_keyboard(current_rotation),
    )


@router.callback_query(F.data.startswith("rotation_"))
async def handle_rotation_callbacks(callback: types.CallbackQuery):
    """Handles clicks on rotation inline buttons"""
    rotation_value = callback.data.split("_")[1]

    result = detection_service.update_camera_rotation(rotation_value)

    if result["success"]:
        await callback.message.edit_text(
            f"✅ {result['message']}\n\nCurrent setting: <b>{rotation_value}</b>",
            reply_markup=get_rotation_inline_keyboard(rotation_value),
        )
    else:
        await callback.answer(f"❌ {result['message']}", show_alert=True)

    await callback.answer()


@router.message(F.text == FRAME_SKIP_BUTTON)
async def frame_skip_command(message: types.Message, state: FSMContext):
    """Handle the frame skip configuration command"""
    result = detection_service.get_frame_skip()

    if result["success"]:
        await state.set_state(BotStates.waiting_for_frame_skip_value)
        await message.answer(
            FRAME_SKIP_INSTRUCTION.format(current_value=result["value"]),
            reply_markup=get_back_keyboard(),
        )
    else:
        await message.answer(
            f"❌ {result['message']}", reply_markup=get_config_keyboard()
        )


@router.message(F.text == SESSION_TIMEOUT_BUTTON)
async def session_timeout_command(message: types.Message, state: FSMContext):
    """Handle the session timeout configuration command"""
    result = detection_service.get_session_timeout()

    if result["success"]:
        await state.set_state(BotStates.waiting_for_session_timeout_value)
        await message.answer(
            SESSION_TIMEOUT_INSTRUCTION.format(current_value=result["value"]),
            reply_markup=get_back_keyboard(),
        )
    else:
        await message.answer(
            f"❌ {result['message']}", reply_markup=get_config_keyboard()
        )


@router.message(F.text == CAMERA_DURATION_BUTTON)
async def camera_duration_command(message: types.Message, state: FSMContext):
    """Handle the camera duration configuration command"""
    result = detection_service.get_camera_duration()

    if result["success"]:
        await state.set_state(BotStates.waiting_for_camera_duration_value)
        await message.answer(
            CAMERA_DURATION_INSTRUCTION.format(current_value=result["value"]),
            reply_markup=get_back_keyboard(),
        )
    else:
        await message.answer(
            f"❌ {result['message']}", reply_markup=get_config_keyboard()
        )


@router.message(F.text == RESET_BUTTON)
async def reset_command(message: types.Message, state: FSMContext):
    """Handle the reset counters command with detailed feedback"""
    plates_before = detection_service.get_all_plates()
    count_before = plates_before.get("total_detections", 0)

    result = detection_service.reset_counters()

    if result["success"]:
        plates_after = detection_service.get_all_plates()
        count_after = plates_after.get("total_detections", 0)

        confirmation_text = (
            f"✅ {result['message']}\n\n"
            f"📊 Statistics before reset: {count_before} total detections.\n"
            f"📊 Statistics after reset: {count_after} total detections."
        )
        await message.answer(confirmation_text, reply_markup=get_start_keyboard())
    else:
        await message.answer(
            f"❌ {result['message']}", reply_markup=get_start_keyboard()
        )


@router.message(F.text == BACK_BUTTON)
async def back_command(message: types.Message, state: FSMContext):
    """Handle the back command"""
    await state.clear()
    await message.answer(
        "🔙 Returning to main menu...", reply_markup=get_start_keyboard()
    )


@router.message(BotStates.waiting_for_video, F.video)
async def process_video(message: types.Message, state: FSMContext):
    """Process a video file with a proactive size check."""

    # --- PROACTIVE FILE SIZE CHECK ---
    file_size_bytes = message.video.file_size
    if file_size_bytes > BotConfig.MAX_VIDEO_SIZE:
        file_size_mb = file_size_bytes / (1024 * 1024)
        await message.answer(
            f"❌ The video file is too large ({file_size_mb:.2f}MB). "
            f"Please send a video smaller than {BotConfig.MAX_VIDEO_SIZE_MB}MB."
        )
        # DO NOT reset the state when rejecting a large file
        return
    # --- END OF CHECK ---

    await message.answer(PROCESSING_VIDEO)

    try:
        file_info = await message.bot.get_file(message.video.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)

        temp_file = create_temp_file(
            downloaded_file.getvalue(), suffix=f".{file_info.file_path.split('.')[-1]}"
        )

        try:
            is_valid, validation_message = validate_video_file(temp_file)
            if not is_valid:
                await message.answer(f"❌ {validation_message}")
                # DO NOT reset the state when rejecting due to format
                return

            result = await detection_service.process_video_file(temp_file)

            if result["success"]:
                if result["plates"]:
                    result_text = "🚗 Detected License Plates:\n\n"
                    for plate, count in result["plates"].items():
                        result_text += f"🔢 {plate}: {count} time(s)\n"

                    await message.answer(result_text)
                else:
                    await message.answer(NO_PLATES_FOUND_WITH_SUGGESTIONS)
            else:
                await message.answer(f"❌ {result['message']}")

        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            await message.answer(
                "❌ An error occurred while processing the video. Please try again."
            )
        finally:
            cleanup_temp_file(temp_file)

    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        await message.answer("❌ Failed to download the video. Please try again.")
    finally:
        # Reset the state only after the entire operation is complete
        await state.clear()
        await message.answer(
            "✅ Processing complete!", reply_markup=get_start_keyboard()
        )


@router.message(BotStates.waiting_for_camera_url, F.text)
async def process_camera(message: types.Message, state: FSMContext):
    """Process a camera URL"""
    camera_url_with_params = message.text.strip()

    # --- STEP 1: Separate URL and parameters ---
    try:
        parsed_url = urlparse(camera_url_with_params)
        base_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
        query_params = parse_qs(parsed_url.query)
    except Exception as e:
        logger.error(f"Error parsing camera URL: {e}")
        await message.answer(
            "❌ Invalid URL format. Please check the URL and try again.",
            reply_markup=get_back_keyboard(),
        )
        return

    # --- STEP 2: Validate only the "clean" URL ---
    validation_result = detection_service.validate_camera_url(base_url)
    if not validation_result["success"]:
        await message.answer(
            f"❌ {validation_result['message']}", reply_markup=get_back_keyboard()
        )
        return

    await message.answer(PROCESSING_CAMERA)

    try:
        # --- STEP 3: Determine duration ---
        # Get the configured duration as the default value
        duration_result = detection_service.get_camera_duration()
        if duration_result["success"]:
            duration_seconds = duration_result["value"]
        else:
            duration_seconds = BotConfig.DEFAULT_CAMERA_DURATION_SECONDS
            logger.warning(
                f"Could not get camera duration from service, using default: {duration_seconds}s"
            )

        # Override the duration if it is present in the URL parameters
        if "duration" in query_params:
            try:
                url_duration = int(query_params["duration"][0])
                if url_duration > 0:
                    logger.info(
                        f"Duration {url_duration}s found in URL, overriding config setting."
                    )

                    # --- Save this value as the new default setting ---
                    update_result = detection_service.update_camera_duration(
                        url_duration
                    )
                    if update_result["success"]:
                        # Inform the user that the default setting has been changed
                        await message.answer(
                            f"⏱️ Default camera duration updated to {url_duration}s for future sessions."
                        )
                    else:
                        # --- Save this value as the new default setting ---
                        logger.error(
                            f"Failed to save new camera duration: {update_result['message']}"
                        )
                    # --- END OF NEW ---

                    duration_seconds = url_duration
                else:
                    logger.warning(
                        f"Invalid duration in URL ({url_duration}), using configured value."
                    )
            except (ValueError, IndexError):
                logger.warning(
                    "Failed to parse duration from URL, using configured value."
                )

        # --- STEP 4: Start processing with clean URL and final duration ---
        logger.info(
            f"Starting camera processing for {duration_seconds} seconds using URL: {base_url}"
        )
        result = await detection_service.process_camera_stream(
            base_url, duration_seconds
        )

        if result["success"]:
            if result["plates"]:
                result_text = "🚗 Detected License Plates:\n\n"
                for plate, count in result["plates"].items():
                    result_text += f"🔢 {plate}: {count} time(s)\n"

                await message.answer(result_text)
            else:
                await message.answer(NO_PLATES_FOUND_WITH_SUGGESTIONS)
        else:
            await message.answer(f"❌ {result['message']}")

    except Exception as e:
        logger.error(f"Error connecting to camera: {str(e)}")
        await message.answer(f"❌ Error connecting to camera: {str(e)}")
    finally:
        await state.clear()
        await message.answer(
            "✅ Processing complete!", reply_markup=get_start_keyboard()
        )


@router.message(BotStates.waiting_for_search_query, F.text)
async def process_search(message: types.Message, state: FSMContext):
    """Process a search query"""
    search_query = message.text.strip()

    result = detection_service.search_license_plate(search_query)

    if result["success"]:
        if result["found"]:
            await message.answer(
                f"✅ License plate '{result['plate']}' found {result['count']} time(s)"
            )
        else:
            await message.answer(
                f"❌ License plate '{result['plate']}' not found in records"
            )
    else:
        await message.answer(f"❌ {result['message']}")

    await state.clear()
    await message.answer("🔍 Search complete!", reply_markup=get_start_keyboard())


@router.message(BotStates.waiting_for_accuracy_value, F.text)
async def process_accuracy_value(message: types.Message, state: FSMContext):
    """Process accuracy value"""
    try:
        accuracy = int(message.text.strip())

        result = detection_service.update_accuracy(accuracy)

        if result["success"]:
            await message.answer(f"✅ {result['message']}")
        else:
            await message.answer(f"❌ {result['message']}")

    except ValueError:
        await message.answer(INVALID_ACCURACY)

    await state.clear()
    await message.answer(SETTINGS_UPDATED, reply_markup=get_config_keyboard())


@router.message(BotStates.waiting_for_frame_skip_value, F.text)
async def process_frame_skip_value(message: types.Message, state: FSMContext):
    """Process frame skip value"""
    try:
        frame_skip = int(message.text.strip())
        result = detection_service.update_frame_skip(frame_skip)

        if result["success"]:
            await message.answer(f"✅ {result['message']}")
            await state.clear()
            await message.answer(SETTINGS_UPDATED, reply_markup=get_config_keyboard())
        else:
            await message.answer(f"❌ {result['message']}")

    except ValueError:
        await message.answer(INVALID_INTEGER)


@router.message(BotStates.waiting_for_session_timeout_value, F.text)
async def process_session_timeout_value(message: types.Message, state: FSMContext):
    """Process session timeout value"""
    try:
        timeout_frames = int(message.text.strip())
        result = detection_service.update_session_timeout(timeout_frames)

        if result["success"]:
            await message.answer(f"✅ {result['message']}")
            await state.clear()
            await message.answer(SETTINGS_UPDATED, reply_markup=get_config_keyboard())
        else:
            await message.answer(f"❌ {result['message']}")

    except ValueError:
        await message.answer(INVALID_INTEGER)


@router.message(BotStates.waiting_for_camera_duration_value, F.text)
async def process_camera_duration_value(message: types.Message, state: FSMContext):
    """Process camera duration value"""
    try:
        duration = int(message.text.strip())
        result = detection_service.update_camera_duration(duration)

        if result["success"]:
            await message.answer(f"✅ {result['message']}")
            await state.clear()
            await message.answer(SETTINGS_UPDATED, reply_markup=get_config_keyboard())
        else:
            await message.answer(f"❌ {result['message']}")

    except ValueError:
        await message.answer(INVALID_INTEGER)


# Handle other messages in specific states
@router.message(BotStates.waiting_for_video)
async def invalid_video(message: types.Message):
    """Handle invalid video input"""
    await message.answer(
        "❌ Please send a video file.", reply_markup=get_back_keyboard()
    )


@router.message(BotStates.waiting_for_camera_url)
async def invalid_camera_url(message: types.Message):
    """Handle invalid camera URL input"""
    await message.answer(
        "❌ Please send a valid camera URL in RTSP format.",
        reply_markup=get_back_keyboard(),
    )


@router.message(BotStates.waiting_for_search_query)
async def invalid_search_query(message: types.Message):
    """Handle invalid search query"""
    await message.answer(
        "❌ Please enter a license plate number to search for.",
        reply_markup=get_back_keyboard(),
    )


@router.message(BotStates.waiting_for_accuracy_value)
async def invalid_accuracy_value(message: types.Message):
    """Handle invalid accuracy value"""
    await message.answer(INVALID_ACCURACY, reply_markup=get_back_keyboard())


@router.message(BotStates.waiting_for_frame_skip_value)
async def invalid_frame_skip_value(message: types.Message):
    """Handle invalid frame skip value"""
    await message.answer(INVALID_INTEGER, reply_markup=get_back_keyboard())


@router.message(BotStates.waiting_for_session_timeout_value)
async def invalid_session_timeout_value(message: types.Message):
    """Handle invalid session timeout value"""
    await message.answer(INVALID_INTEGER, reply_markup=get_back_keyboard())


@router.message(BotStates.waiting_for_camera_duration_value)
async def invalid_camera_duration_value(message: types.Message):
    """Handle invalid camera duration value"""
    await message.answer(INVALID_INTEGER, reply_markup=get_back_keyboard())


@router.message(F.text)
async def unknown_message_handler(message: types.Message, state: FSMContext):
    """
    Fallback handler for any text message that is not recognized.
    It only works if the bot is not in a specific state waiting for input.
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(UNKNOWN_COMMAND_MESSAGE, reply_markup=get_start_keyboard())


