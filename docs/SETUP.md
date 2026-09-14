# Batcave Cloud — Setup & Reproduction Guide

This guide explains how to reproduce Batcave Cloud (v0.4.3) from scratch on **Windows**, **Linux**, **macOS**, and **Android (Termux)**. It also preserves the historical hardware documentation of the original deployment on an Android tablet.

---

## Part 1: Quick Reproduction Guide (Any Platform)

Follow these steps on a fresh system to clone and run Batcave Cloud.

### 1. Prerequisites
- **Python**: Version 3.10 or newer (tested up to Python 3.14).
- **Git**: Installed and available on your system path.

### 2. Clone the Repository
```bash
git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
cd Batcave_Cloud
```

### 3. Create Virtual Environment & Install Dependencies
Create a Python virtual environment to avoid installing packages into your global system Python.

- **Linux / macOS / Termux**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements-dev.txt
  ```

- **Windows (PowerShell)**:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements-dev.txt
  ```

*(Note: If you only plan to run the server and not execute tests, you can install `requirements.txt` instead of `requirements-dev.txt`.)*

### 4. Generate Private Configuration
Batcave Cloud refuses to boot without a secret key and password hash. Generate a private configuration file outside the repository:

- **Linux / macOS / Termux**:
  ```bash
  python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
  export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave.env
  ```

- **Windows (PowerShell)**:
  ```powershell
  python -m server.manage create-config --output "$HOME\.config\batcave-cloud\batcave.env"
  $env:BATCAVE_CONFIG_FILE = "$HOME\.config\batcave-cloud\batcave.env"
  ```

When prompted, enter a password for your single-user workspace.

### 5. Configure Storage Location (Non-Android Systems)
By default, `BATCAVE_DATA_ROOT` points to `/storage/emulated/0/BatCave` (the Android shared storage path). On other operating systems, set this variable to a local directory of your choice:

- **Linux / macOS**:
  ```bash
  export BATCAVE_DATA_ROOT=~/BatCave
  ```

- **Windows (PowerShell)**:
  ```powershell
  $env:BATCAVE_DATA_ROOT = "$HOME\BatCave"
  ```

Batcave Cloud will automatically create the storage root and its subdirectories (`files`, `photos`, `notes`, `ideas`, `projects`, `backups`, `archive`) upon startup.

### 6. Run Automated Tests
Verify that your local environment is functioning correctly by running the test suite:

```bash
python -m pytest -q
```
Expected result: `51 passed`.

### 7. Start the Server
```bash
python -m server.app
```

The server binds by default to `0.0.0.0:8080`. Open your browser and navigate to:
- Locally: `http://localhost:8080` (or `http://127.0.0.1:8080`)
- Over LAN: `http://<server-ip>:8080`

Log in using the password you configured in Step 4.

---

## Part 2: Platform-Specific Guides

### Windows (PowerShell)

1. Open PowerShell and navigate to your projects directory:
   ```powershell
   git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
   cd Batcave_Cloud
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   *(If script execution is disabled, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.)*
3. Install dependencies:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
   ```
4. Create your private configuration:
   ```powershell
   .\.venv\Scripts\python.exe -m server.manage create-config --output "$HOME\.config\batcave-cloud\batcave.env"
   ```
5. Set environment variables and run:
   ```powershell
   $env:BATCAVE_CONFIG_FILE = "$HOME\.config\batcave-cloud\batcave.env"
   $env:BATCAVE_DATA_ROOT = "$HOME\BatCave"
   .\.venv\Scripts\python.exe -m server.app
   ```

### Linux (Debian, Ubuntu, Arch, Fedora)

1. Ensure Python 3 and venv are installed:
   ```bash
   # Debian / Ubuntu
   sudo apt update && sudo apt install -y python3 python3-venv git
   ```
2. Clone and set up:
   ```bash
   git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
   cd Batcave_Cloud
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
3. Generate config and run:
   ```bash
   python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
   export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave.env
   export BATCAVE_DATA_ROOT=~/BatCave
   python -m server.app
   ```

### macOS (Apple Silicon & Intel)

1. Ensure Xcode Command Line Tools are installed:
   ```bash
   xcode-select --install
   ```
2. Clone and set up:
   ```bash
   git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
   cd Batcave_Cloud
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
3. Generate config and run:
   ```bash
   python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
   export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave.env
   export BATCAVE_DATA_ROOT=~/BatCave
   python -m server.app
   ```

### Android (Termux)

Batcave Cloud was originally created and hosted on an Android device running Termux.

1. **Install Termux**:
   - Install **Termux from F-Droid** (do NOT use the obsolete Google Play Store build).
2. **Update Termux & Install Base Packages**:
   ```bash
   pkg update && pkg upgrade -y
   pkg install -y python git openssh libjpeg-turbo
   ```
   *(Note: `libjpeg-turbo` is required for Pillow to compile or load JPEG support on aarch64 Android).*
3. **Grant Storage Access**:
   ```bash
   termux-setup-storage
   ```
   This links Android shared storage to `~/storage/shared`, which points to `/storage/emulated/0`.
4. **Clone the Repository**:
   ```bash
   git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git ~/Batcave_Cloud
   cd ~/Batcave_Cloud
   ```
5. **Set Up Python Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
6. **Generate Configuration**:
   ```bash
   python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
   export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave.env
   ```
   *(On Android/Termux, `BATCAVE_DATA_ROOT` defaults to `/storage/emulated/0/BatCave`, keeping user files in shared storage accessible by other Android apps).*
7. **Keep Termux Running in Background**:
   To prevent Android's battery optimizer from killing the server when the screen is turned off:
   - Disable Android battery optimizations for Termux (`Settings > Apps > Termux > Battery > Unrestricted`).
   - Acquire a Termux wake-lock before running:
     ```bash
     termux-wake-lock
     ```
8. **Start the Server**:
   ```bash
   python -m server.app
   ```
9. **Access from Android Browser**:
   Open Chrome or Firefox on the tablet and visit:
   ```text
   http://localhost:8080
   ```
   To access it from other computers or phones on the same Wi-Fi network, find the tablet's local IP address (`ip addr show wlan0` or `ifconfig`) and open `http://<tablet-ip>:8080`.

---

## Part 3: Historical Hardware Notes (The Original Batcave Server)

Batcave Cloud was originally conceptualized and deployed on a repurposed tablet. The original physical hardware notes are documented below for historical and engineering context.

### Original Hardware Profile
- **Device**: Samsung Galaxy Tab S6 Lite
- **Model**: SM-P615 (LTE / Wi-Fi)
- **CPU**: Samsung Exynos 9611 (8 cores, ARM Cortex-A73 / Cortex-A53, `aarch64`)
- **RAM**: 4 GB
- **Internal Storage**: 64 GB internal flash storage
- **Operating System**: Android 13 / One UI 5.1.1 (Linux Kernel 4.14.113)
- **Physical Condition**: Broken LCD screen, but touch, digitizer, battery, Wi-Fi, and processor remained fully functional.
- **Network**: Connected continuously to home Wi-Fi via an Airtel Black router.

### Original Architectural Decisions
1. **No Rooting Required**: Android was kept intact as the base operating system. Termux provided the userspace Linux environment without voiding Knox or modifying device partitions.
2. **Storage Separation**:
   - Code & Git repository resided inside Termux private storage: `~/Batcave_Cloud/`.
   - Personal user data resided on Android shared storage: `/storage/emulated/0/BatCave/`.
   - This separation ensured that git commands never tracked personal files or photos.
3. **Remote Administration over SSH**:
   - OpenSSH server was run inside Termux on port `8022`.
   - The primary development machine (a Windows PC) administered the tablet remotely:
     ```bash
     ssh -p 8022 u0_a243@192.168.1.18
     ```
   - ED25519 SSH keys were used for GitHub authentication.
4. **Thermal & Stability Testing**:
   - Tested continuous execution using `termux-wake-lock` and verified background execution while the display was powered down.
   - Long-duration testing verified that the Exynos processor stayed cool and stable under normal Flask HTTP workloads.
