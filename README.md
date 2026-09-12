# 🦇 Batcave Cloud

A self-hosted personal cloud built from an old Samsung Galaxy Tab S6 Lite.

## Vision

Batcave Cloud aims to turn an unused Android tablet into a private, always-on personal server for:

- 📁 Files
- 📷 Photos
- 📝 Notes
- 💡 Ideas
- 🛠️ Projects
- 💾 Backups

The system will eventually be accessible securely from anywhere through a web interface.

## Hardware

- Samsung Galaxy Tab S6 Lite (SM-P615)
- 64 GB internal storage
- Android 13
- Home Wi-Fi

## Current Architecture

```text
Internet
   │
Secure remote access
   │
Home Router
   │
Wi-Fi
   │
Galaxy Tab S6 Lite
   │
Android
   │
Termux
   │
Batcave Cloud
   │
Personal Storage
```

## Goals
- Learn Linux and server administration through practice
- Build a real personal cloud
- Understand networking and secure remote access
- Build the web interface from scratch
- Document the engineering process

## Foundation v0.2 and Files v0.3

The application now has a one-user local login, CSRF protection, safer uploads,
SQLite migrations, and an automated test suite. See [the run and configuration
guide](docs/RUNNING.md) before starting it.

Files v0.3 adds safe breadcrumbs, sorting, hierarchy search, move operations,
metadata, and a filesystem storage summary.
