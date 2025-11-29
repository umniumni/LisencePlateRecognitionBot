# Use the lightweight official Python 3.11 image based on Debian Bookworm
FROM python:3.11-slim-bookworm

# Set the working directory. This is the location where your code will be mounted.
WORKDIR /app

# Install system dependencies for OpenCV, git, sudo, and build tools.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    git \
    build-essential \
    curl \
    unzip \
    sudo \
    python3-pip \
    python3-wheel \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(ALL\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Add the user's local folder to PATH so that pip packages are accessible
ENV PATH="/home/$USERNAME/.local/bin:${PATH}"

# Add the working directory (/app) to PYTHONPATH. 
# This will solve the module import problem, for example, "src.main".
ENV PYTHONPATH=/app:${PYTHONPATH}

# Switch to the non-root user
USER $USERNAME



