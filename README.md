
# 🚗 License Plate Recognition Telegram Bot

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![aiogram 3.3.0](https://img.shields.io/badge/aiogram-3.3.0-00a8e8.svg)](https://aiogram.dev)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

A powerful Telegram bot that detects and recognizes license plates from videos and live camera streams using YOLOv8, EasyOCR and OpenCV. This bot can recognize Uzbekistan license plates.

## 📋 Features

- 🎥 **Video Detection**: Upload video files to detect license plates
- 📷 **Camera Detection**: Connect to RTSP camera streams for real-time detection
- 🔍 **Search Functionality**: Search for specific license plates in detection history
- 🔄 **Reset Counters**: Clear all detection data with one click
- ⚙️ **Configurable Settings**: Adjust accuracy, frame skip, session timeout, and camera rotation
- 💾 **Local Storage**: All data stored locally in JSON files
- 🎯 **Uzbekistan Plates**: Specialized for Uzbekistan license plate formats
- 🔄 **Camera Rotation**: Support for rotating camera feeds (90°, 180°, 270°)
- ⏱️ **Session Management**: Smart detection sessions to avoid duplicate counting
- 📊 **Statistics**: View detection statistics and history

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show the main menu and start using the bot |
| `/help` | Display help information and available commands |
| `/status` | Show current bot configuration and status |
| `/stats` | Display recent detection statistics |

## 🏗️ Project Structure

```
LisencePlateRecognitionBot/
├── .devcontainer/              # Dev Container configuration
│   └── devcontainer.json       # VS Code Dev Container settings
├── config/                     # Configuration files
│   ├── __init__.py            # Package initialization
│   ├── bot_config.py          # Bot configuration settings
│   ├── buttons.py             # Button text definitions
│   └── messages.py            # Bot message templates
├── data/                       # Data storage directory
│   ├── camera_duration_config.json  # Camera duration settings
│   ├── license_plates.json     # Detected plates storage
│   └── rotation_config.json    # Camera rotation settings
├── src/                        # Source code
│   ├── __init__.py            # Package initialization
│   ├── bot/                   # Bot implementation
│   │   ├── __init__.py        # Package initialization
│   │   ├── handlers.py        # Telegram bot handlers
│   │   ├── keyboards.py       # Keyboard layouts
│   │   ├── main.py           # Bot entry point
│   │   └── utils.py          # Utility functions
│   ├── detection/             # Detection logic
│   │   ├── __init__.py        # Package initialization
│   │   ├── detector.py        # Detection service
│   │   └── models.py          # YOLO models implementation
│   └── storage/               # Storage management
│       ├── __init__.py        # Package initialization
│       └── storage_manager.py # JSON storage manager
├── weights/                    # ML model files
│   ├── detection.pt          # License plate detection model
│   └── recognition.pt        # Character recognition model
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
├── Dockerfile                 # Docker configuration
├── README.md                  # This file
└── requirements.txt           # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- [Visual Studio Code](https://code.visualstudio.com/) (latest version)
- [Docker](https://www.docker.com/products/docker-desktop) installed and running
- [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) VS Code extension
- A Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Step 1: Clone the Repository

```bash
git clone https://github.com/umniumni/LisencePlateRecognitionBot.git
cd LisencePlateRecognitionBot
```

or

1. Go to the [repository page](https://github.com/umniumni/LisencePlateRecognitionBot.git) on `GitHub`. 
2. Click the green `<> Code` button and select `Download ZIP`. 
3. Unzip the downloaded file on your computer. 
4. Open the project folder in `Visual Studio Code`. 

### Step 2: Open in VS Code with Dev Containers

1. Open the project folder in VS Code
2. When prompted, click "Reopen in Container"
3. VS Code will automatically build the Docker container and set up the environment
4. If something goes wrong, press F1 → select Dev Containers: Rebuild and Reopen in Container

### Step 3: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your bot token:
   ```env
   BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"
   ```

### Step 4: Run the Bot

```bash
python src/bot/main.py
```

## 🐳 Docker Setup

### What is Docker?

Docker is a platform that uses containerization technology to create and run applications in isolated environments called containers. Think of it as a lightweight virtual machine that contains everything your application needs to run.

### What is Dev Container?

Dev Container is a VS Code feature that allows you to use a Docker container as a full-featured development environment. This means:
- Everyone on your team uses the exact same development environment
- No need to install Python or dependencies on your local machine
- Consistent behavior across different machines
- Easy to reproduce and share development setups

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# 🤖 Telegram Bot Token - Get yours from BotFather
BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"

# 🎬 Maximum video file size in Megabytes
MAX_VIDEO_SIZE_MB=20
```

### Bot Settings

The bot provides an interactive configuration menu where you can adjust:

- **🎯 Accuracy**: Detection confidence threshold (0-100%)
- **🖼️ Frame Skip**: Number of frames to skip for faster processing
- **⏱️ Session Timeout**: Frames to wait before ending a detection session
- **🔄 Camera Rotation**: Rotate camera feed (Off, 90°, 180°, 270°)
- **⏱️ Camera Duration**: Default duration for camera processing

## 📱 How to Use the Bot

### 1. Video Detection

1. Click the **📹 Video Detection** button
2. Upload a video file (MP4, AVI, MOV, MKV)
3. Wait for processing
4. View detected license plates and counts

### 2. Camera Detection

1. Click the **📷 Camera Detection** button
2. Send an RTSP camera URL (e.g., `rtsp://192.168.1.100:554/stream`)
3. Optional: Add `?duration=N` to set processing time in seconds
4. Wait for real-time processing
5. View detected license plates

### 3. Search Plates

1. Click the **🔍 Search** button
2. Enter a license plate number
3. Get search results with detection count

### 4. Reset Counters

1. Click the **🔄 Reset Counters** button
2. Confirm to clear all detection data

### 5. Configure Settings

1. Click the **⚙️ Configuration** button
2. Select a setting to adjust
3. Follow the instructions to update

## 🔧 Development

### Code Structure

- **`config/`**: All configuration files including button texts and messages
- **`src/bot/`**: Telegram bot implementation using aiogram 3
- **`src/detection/`**: YOLOv8-based detection and recognition logic
- **`src/storage/`**: Local JSON storage management
- **`weights/`**: Pre-trained models for detection and recognition

### Best Practices Used

- ✅ Clean architecture with separation of concerns
- ✅ Configuration management with environment variables
- ✅ Error handling and logging
- ✅ Async/await for non-blocking operations
- ✅ Type hints for better code maintainability
- ✅ Modular design for easy testing and maintenance
- ✅ FSM (Finite State Machine) for user interaction flows
- ✅ Lazy loading of ML models for faster startup

## 🛠 Troubleshooting

### Common Issues

1. **Bot doesn't start**
   - Check your `BOT_TOKEN` in `.env` file
   - Ensure Docker is running
   - Check logs for error messages
   - Press F1 → select Dev Containers: Rebuild and Reopen in Container

2. **Detection not working**
   - Verify model files are in `weights/` directory
   - Check file permissions
   - Ensure video format is supported

3. **Camera connection fails**
   - Verify RTSP URL format
   - Check network connectivity
   - Ensure camera is accessible

4. **Memory issues**
   - Reduce video file size
   - Increase frame skip setting
   - Use smaller duration for camera processing

### Debug Mode

Enable debug logging by setting in `.env`:
```env
LOG_LEVEL="DEBUG"
```

## 📚 Acknowledgments

- [YOLOv8](https://github.com/ultralytics/ultralytics) for object detection
- [aiogram](https://github.com/aiogram/aiogram) for Telegram bot framework
- [OpenCV](https://opencv.org/) for computer vision operations
- [inomjonramatov.uz](https://inomjonramatov.uz/tutorial/license_plate_recognition/)

