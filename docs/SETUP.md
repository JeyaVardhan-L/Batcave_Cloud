# Batcave Cloud — Initial Setup

## 1. Project

**Batcave Cloud** is a personal cloud-storage and self-hosted infrastructure project built around an unused Samsung Galaxy Tab S6 Lite.

The goal is to turn the tablet into an always-on personal server that can be accessed securely from anywhere.

The project is also a hands-on learning project for Linux, networking, Git, server administration, web development, and security.

---

## 2. Hardware

- Device: Samsung Galaxy Tab S6 Lite
- Model: SM-P615
- Storage: 64 GB internal storage
- microSD: None
- Network: Home Wi-Fi
- Router: Airtel Black
- Display: Broken, but tablet remains functional
- Approximate free storage at setup: 39 GB

The tablet remains usable despite the broken screen and is intended to stay powered and connected to home Wi-Fi as the Batcave Cloud server.

---

## 3. Software Environment

- Android: 13
- One UI: 5.1.1
- Kernel: 4.14.113
- CPU architecture: aarch64
- Termux: Installed from F-Droid

### Architecture decision

The first version will **not root or replace Android**.

Instead, Android remains the host operating system and Termux provides a Linux userspace in which server software can run.

Conceptually:

```text
Android 13
    |
    +-- Termux
          |
          +-- Linux userspace
          +-- SSH
          +-- Server software
          +-- Git
          +-- Batcave Cloud application
```

This approach keeps the tablet usable while allowing the project to explore Linux and server administration.

---

## 4. Initial Termux Setup

Termux packages were updated using:

```bash
pkg update
pkg upgrade
```

Android shared-storage access was enabled using:

```bash
termux-setup-storage
```

Termux exposes Android shared storage through:

```text
~/storage/shared
```

which points to:

```text
/storage/emulated/0
```

The tablet's user-data partition reports approximately:

```text
52 GB total
39 GB available
```

The 100%-used system partitions shown by `df -h` are Android system/read-only partitions and are separate from the user storage available to Batcave Cloud.

---

## 5. Bat Cave Storage Structure

Personal data is deliberately kept **outside the Git repository**.

Current structure:

```text
/storage/emulated/0/BatCave/
├── files/
├── photos/
├── notes/
├── ideas/
├── projects/
├── backups/
└── archive/
```

Repository and personal data are intentionally separated:

```text
~/Batcave_Cloud/              # Code + documentation
/storage/emulated/0/BatCave/  # Personal data
```

Personal files must never be committed to GitHub.

---

## 6. Android Server Preparation

Termux was configured with:

- Battery usage: **Unrestricted**
- Developer Options: **Stay awake enabled**
- Developer Options: **Don't keep activities disabled**

The Termux wake-lock capability was tested using:

```bash
termux-wake-lock
```

A background execution test was performed:

```bash
sleep 60 && echo "BATCAVE STILL ALIVE"
```

The tablet successfully printed:

```text
BATCAVE STILL ALIVE
```

after the screen had been turned off.

This demonstrated that Termux could continue executing a process while the display was off.

### Reliability note

The tablet experienced two unexpected shutdowns during initial setup while under relatively high interactive load. It recovered normally after a force restart. The device has also demonstrated that it can remain operational for extended periods under normal use.

Because Batcave Cloud is intended to be an always-on server, long-duration stability and thermal/power behavior will be tested before the system is trusted with important data.

---

## 7. SSH Administration

OpenSSH was installed in Termux:

```bash
pkg install openssh
```

The SSH server was started using:

```bash
sshd
```

Termux SSH uses port **8022**.

The tablet's local Wi-Fi address during setup was:

```text
192.168.1.18
```

An SSH password was configured using:

```bash
passwd
```

The Windows PC successfully connected to the tablet using:

```bash
ssh -p 8022 u0_a243@192.168.1.18
```

This established remote administration over the home Wi-Fi network:

```text
Windows PC
    |
    | SSH :8022
    v
Airtel Black Router
    |
    | Wi-Fi
    v
Galaxy Tab S6 Lite
    |
    v
Termux
```

The Termux username is:

```text
u0_a243
```

---

## 8. Git Setup

Git was installed in Termux.

Git identity was configured as:

```text
Name:  JeyaVardhan-L
Email:  GitHub noreply address
```

The GitHub repository is:

```text
JeyaVardhan-L/Batcave_Cloud
```

The repository was cloned onto the tablet using SSH:

```bash
git clone git@github.com:JeyaVardhan-L/Batcave_Cloud.git
```

The repository was initially empty, which was expected.

---

## 9. GitHub SSH Authentication

An ED25519 SSH key was generated on the tablet:

```bash
ssh-keygen -t ed25519 -C "GitHub noreply address"
```

The **public key** was added to GitHub as an authentication key.

GitHub authentication from the tablet was successfully verified with:

```bash
ssh -T git@github.com
```

GitHub responded with a successful authentication message.

The private SSH key remains on the tablet and must never be committed, uploaded, or shared.

---

## 10. Repository Structure

The initial repository structure is:

```text
Batcave_Cloud/
├── .git/
├── .gitignore
├── README.md
├── docs/
├── scripts/
├── server/
└── web/
```

Purpose:

- `docs/` — architecture, setup, networking, security, troubleshooting, and learning documentation
- `scripts/` — automation and maintenance scripts
- `server/` — backend/server software
- `web/` — web interface
- `README.md` — project overview
- `.gitignore` — protection against accidentally tracking secrets or personal data

---

## 11. Git Safety

The initial `.gitignore` contains:

```gitignore
# Personal Bat Cave data

BatCave/
*.key
*.pem
.env
.env.*
```

The actual personal storage directory is outside the repository, but the ignore rule provides an additional safety layer.

Credentials, private keys, environment files, and personal Bat Cave data must not be committed to GitHub.

---

## 12. Current Architecture

The initial target architecture is:

```text
                         INTERNET
                             |
                    Secure remote access
                             |
                             v
                    Home Airtel Router
                             |
                            Wi-Fi
                             |
                             v
                 Samsung Galaxy Tab S6 Lite
                             |
                          Android
                             |
                          Termux
                         /                             SSH      Server
                        |          |
                     Admin    Batcave Cloud
                                   |
                           Personal Storage
                                   |
                  /storage/emulated/0/BatCave
```

Remote access will eventually be provided through a secure mechanism such as a VPN or outbound tunnel rather than directly exposing the tablet's SSH/server ports to the public internet.

---

## 13. Completed Milestones

- [x] Tablet selected
- [x] Hardware/software environment inspected
- [x] Termux installed from F-Droid
- [x] Termux packages updated
- [x] Android shared-storage access configured
- [x] Approximately 39 GB free storage confirmed
- [x] BatCave storage directories created
- [x] Termux battery usage set to Unrestricted
- [x] Stay awake enabled
- [x] Don't keep activities disabled
- [x] Wake-lock tested successfully
- [x] OpenSSH installed
- [x] SSH server started
- [x] Windows-to-tablet SSH access tested successfully
- [x] Git installed
- [x] Git identity configured
- [x] GitHub ED25519 authentication configured
- [x] GitHub SSH authentication verified
- [x] Batcave_Cloud repository cloned to tablet
- [x] Initial repository structure created
- [x] Initial Git safety rules created

---

## 14. Next Objectives

### Phase 1 — Reliable server foundation

1. Make Termux and required services start reliably after reboot.
2. Improve Android power-management configuration.
3. Verify long-duration stability.
4. Establish basic monitoring and health checks.

### Phase 2 — Local Batcave Cloud server

1. Choose the backend architecture.
2. Build a minimal local web server.
3. Implement file listing.
4. Implement file upload/download.
5. Connect the application to the BatCave storage directory.

### Phase 3 — Web interface

Target sections include:

- Photos
- Files
- Notes
- Ideas
- Projects
- Backups
- Archive

Future features may include search, previews, metadata, storage statistics, and mobile-friendly access.

### Phase 4 — Security and remote access

1. Authentication and authorization
2. HTTPS
3. Secure remote connectivity
4. Minimize exposed services
5. Secrets management
6. Access logging
7. Backup and recovery strategy

### Phase 5 — Automation and reliability

Potential future features:

- Automatic phone photo backup
- Scheduled backups
- Storage monitoring
- Health monitoring
- Automatic service restart
- Notifications
- Database/indexing if needed

---

## 15. Engineering Principles

Batcave Cloud is being built incrementally.

The goal is not to blindly copy commands or deploy a black-box application. Each major component should be understood before it is automated.

The project is intended to provide practical experience with:

- Linux
- Android/Linux interaction
- Shell
- Git and GitHub
- SSH
- Networking
- HTTP/HTTPS
- Web development
- Authentication
- Security
- Storage management
- Backups
- System reliability
- Server administration

The repository should document both **what was built** and **why it was built that way**.

---

## 16. Important Security Rule

The Batcave contains personal data.

Before exposing it to the internet, the project must have:

1. Strong authentication
2. Encrypted transport
3. A deliberate remote-access architecture
4. A backup strategy
5. A recovery plan

**The Batcave should never be made publicly accessible just to make the first demo work.**
