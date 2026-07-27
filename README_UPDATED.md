# Safe Media Transfer - Updated & Secure Edition

**Version:** 2.0.0 | **Released:** July 25, 2026

A secure, Python-based application for safely transferring videos and images between PCs, especially designed for scenarios where one PC may have malware or viruses.

---

## 📋 What's New in v2.0.0

### 🔒 Security Enhancements

- **Path Traversal Prevention**: New `PathSecurityValidator` module prevents directory escape attacks
- **Enhanced File Type Detection**: `python-magic-bin` library for accurate MIME type verification
- **Improved Input Validation**: All paths and file names validated before processing
- **Better Error Handling**: Security violations logged with full context
- **Configuration Validation**: Config file validated at startup for secure defaults

### 📦 Dependency Updates

- PySide6: 6.11.1 (latest stable GUI framework)
- Added `python-magic-bin` (0.4.14) for file type detection
- Added `pydantic` (2.9.0) for data validation
- Added `cryptography` (43.0.0) for security operations

### 📚 Documentation

- **QUICKSTART.md**: Get started in 5 minutes
- **SETUP_GUIDE.md**: Comprehensive setup and configuration guide
- **SECURITY.md**: Detailed security implementation documentation
- **README_UPDATED.md**: This file

### 🎯 Workflow Improvements

- Clearer separation between video and image transfers
- Better progress indication
- Enhanced logging and diagnostics
- Improved error messages

---

## ✨ Key Features

### Security Features
✅ **Path Traversal Protection** - Prevents access to files outside selected directory
✅ **SHA256 Verification** - Every file is verified for integrity after transfer
✅ **File Type Validation** - Only approved image and video formats allowed
✅ **Executable Blocking** - All .exe, .dll, .bat, .cmd, .ps1, etc. blocked
✅ **Archive Blocking** - No .zip, .rar, .7z, .iso files can be transferred
✅ **Directory Isolation** - No access to system folders or files outside scope
✅ **Secure Defaults** - Application is secure by default

### Transfer Features
✅ **Separate Workflows** - Videos and images handled separately
✅ **Chunk-Based Transfer** - 4MB chunks for optimal performance
✅ **Resume Support** - Interrupted transfers can be resumed
✅ **Duplicate Handling** - Configure how to handle existing files
✅ **Large File Support** - Transfer files up to 1TB
✅ **Batch Transfers** - Send multiple files at once
✅ **Progress Tracking** - Real-time progress indication

### User Experience
✅ **GUI Interface** - Visual application (PySide6)
✅ **No Executables** - Run from terminal with Python (no .exe needed)
✅ **Cross-Platform** - Works on Windows, macOS, Linux
✅ **Comprehensive Logging** - All transfers logged for auditing
✅ **Easy Configuration** - Simple TOML config file
✅ **Detailed Help** - Complete documentation included

---

## 🏗️ Architecture

### Application Structure

```
safe_media_transfer/
├── app/
│   ├── config/          # Configuration loading & validation
│   ├── integrity/       # Hash verification (SHA256)
│   ├── logging_setup/   # Logging configuration
│   ├── models/          # Data models & schemas
│   ├── networking/      # Socket transport layer
│   ├── protocol/        # Transfer protocol implementation
│   ├── scanning/        # File discovery & scanning
│   ├── security/        # 🆕 NEW! Path validation & security checks
│   ├── state/           # Resume & state management
│   ├── transfer/        # Send/receive logic
│   ├── ui/              # PySide6 GUI components
│   ├── utils/           # Utility functions
│   └── validation/      # File extension & signature validation
├── tests/               # Unit tests
├── logs/                # Application logs
├── config.toml          # Configuration file
├── config.example.toml  # Example configuration
├── sender_main.py       # Sender entry point
├── receiver_main.py     # Receiver entry point
├── requirements.txt     # Python dependencies
├── QUICKSTART.md        # 5-minute getting started
├── SETUP_GUIDE.md       # Complete setup guide
├── SECURITY.md          # Security documentation
└── README_UPDATED.md    # This file
```

### Security Flow

```
SENDER                              RECEIVER
  │                                   │
  ├─ User selects folder              │
  │                                   │
  ├─ Scanner finds files              │
  │  └─ File type validation          │
  │  └─ Path validation               │
  │                                   │
  └─ Send to receiver ────────────→ Listen for connection
                                     │
                                     ├─ Receive manifest
                                     ├─ Validate paths
                                     │
                          Receive file chunks ←─ ─
                          │  (with progress)
                          ├─ Save to .part file
                          ├─ Compute SHA256
                          ├─ Compare hashes
                          │
                          ├─ If match: Rename to final
                          └─ If mismatch: Reject & log
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ ([download](https://www.python.org/downloads/))
- Both PCs on same network
- ~30MB disk space for application

### Installation (2 minutes)

```bash
# 1. Extract zip file
# 2. Open terminal in extracted folder
# 3. Install dependencies

pip install -r requirements.txt
```

### Configuration (1 minute)

**RECEIVER PC:**
```toml
[app]
mode = "receiver"

[storage]
default_destination = "C:\\Transfers"
```

**SENDER PC:**
```toml
[app]
mode = "sender"

[network]
receiver_ip = "192.168.1.5"  # Receiver's IP
```

### Run (30 seconds each)

```bash
# Receiver: python receiver_main.py
# Sender:   python sender_main.py
```

→ See `QUICKSTART.md` for complete walkthrough

---

## 📖 Documentation

| Document | Purpose | Time |
|----------|---------|------|
| [QUICKSTART.md](QUICKSTART.md) | Get running in 5 minutes | 5 min |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Detailed setup & usage | 20 min |
| [SECURITY.md](SECURITY.md) | Security implementation details | 15 min |

---

## 🔐 Security Details

### What We Protect Against

✅ **Path Traversal Attacks**
```
Attack: ../../../windows/system32/malware
Result: ❌ BLOCKED - Path escapes allowed directory
```

✅ **Executable Injection**
```
Attack: malware.exe (renamed as .mp4)
Result: ❌ BLOCKED - MIME type detected as executable
```

✅ **Data Corruption**
```
Attack: Malware modifies file during transfer
Result: ❌ BLOCKED - SHA256 hash mismatch detected
```

✅ **Directory Escape via Symlinks**
```
Attack: Symlink pointing to /etc/passwd
Result: ❌ BLOCKED - Symlinks are validated/blocked
```

✅ **Archive Bombs**
```
Attack: malware.zip (renamed as .mp4)
Result: ❌ BLOCKED - File type validation detects archive
```

### What We DON'T Protect Against

❌ **Network Eavesdropping** (data sent in plaintext)
- Solution: Use VPN or isolated network

❌ **Malware on Sender** (can still see file names)
- Solution: Assume network is private

❌ **0-Day Exploits** (unknown Python/OS vulnerabilities)
- Solution: Keep OS and Python updated

### Security Standards

- **Hashing**: SHA256 (FIPS 180-4 compliant)
- **Validation**: OWASP-compliant input validation
- **Architecture**: Defense in depth with multiple validation layers

→ See [SECURITY.md](SECURITY.md) for complete security documentation

---

## 📋 Configuration Reference

### Essential Settings

```toml
[app]
mode = "receiver"  # or "sender"

[network]
receiver_ip = "192.168.1.5"  # For sender: receiver's IP
port = 5001

[storage]
default_destination = "C:\\Transfers"

[transfer]
chunk_size_bytes = 4194304  # 4MB
duplicate_policy = "replace"  # replace/skip/fail
```

### All Settings

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete reference and examples.

---

## 🐛 Troubleshooting

### Connection Issues
```
Error: Connection refused
→ Check receiver is running
→ Verify IP address in config
→ Check firewall allows port 5001
```

### Transfer Issues
```
Error: Hash mismatch
→ Network error occurred (file is safe)
→ Transfer can be resumed
→ Try again with better network
```

### Performance Issues
```
Issue: Slow transfer speed
→ Use wired connection (not WiFi)
→ Close other applications
→ Check disk speed (run CrystalDiskInfo)
→ Reduce other network usage
```

→ See [SETUP_GUIDE.md](SETUP_GUIDE.md) for more troubleshooting

---

## 💻 System Requirements

### Minimum
- Python 3.9+
- 4GB RAM
- 30MB disk space
- Network connection

### Recommended
- Python 3.11+ (faster)
- 8GB+ RAM
- 100MB free disk space
- Wired Ethernet connection
- Windows 10+/macOS 10.15+/Ubuntu 20.04+

### Not Supported
- Python 3.8 or earlier
- Running on same PC (use USB drive instead)
- Internet transfers (too risky for malware scenario)

---

## 📊 Performance Metrics

### Typical Speeds

| Connection | Speed | 10GB Time |
|---|---|---|
| USB 3.0 | 100-400 MB/s | 25-100 sec |
| Gigabit Ethernet | 100-125 MB/s | 80-100 sec |
| WiFi 6 (802.11ax) | 50-100 MB/s | 100-200 sec |
| WiFi 5 (802.11ac) | 20-50 MB/s | 200-500 sec |
| WiFi (802.11n) | 10-30 MB/s | 330-1000 sec |

### Large File Support

- Maximum file size: 1TB (configurable)
- Maximum number of files: 10,000 per transfer
- Minimum chunk size: 64KB
- Maximum chunk size: 512MB

---

## 📝 Changes from v1.0.0

### New Features
✨ Path traversal protection
✨ Enhanced file type detection
✨ Better error handling
✨ Improved logging
✨ Configuration validation
✨ Comprehensive documentation

### Breaking Changes
- Config format remains compatible
- Sender/receiver entry points unchanged
- Network protocol improved but backward compatible

### Migration from v1.0.0

1. Backup your `config.toml`
2. Extract v2.0.0 over v1.0.0
3. Run: `pip install -r requirements.txt --upgrade`
4. Review `SECURITY.md` for new security features
5. Test with a small transfer first

---

## 🤝 Contributing

To improve this application:

1. Test thoroughly with your files
2. Report issues with detailed logs
3. Suggest security improvements
4. Help improve documentation

---

## ⚖️ License

This application is provided as-is for secure file transfers.

---

## 📞 Support

### Documentation
- See QUICKSTART.md for 5-minute setup
- See SETUP_GUIDE.md for detailed guide
- See SECURITY.md for security details

### Troubleshooting
- Check logs in `logs/` folder
- Enable debug_logging in config.toml
- Review SETUP_GUIDE.md troubleshooting section

### Reporting Issues
1. Describe what you were trying to do
2. Include relevant log entries
3. List your configuration
4. Mention your OS and Python version

---

## ✅ Verification Checklist

Before transferring important files:

- [ ] Both PCs on isolated network
- [ ] Python 3.9+ installed on both
- [ ] `pip install -r requirements.txt` completed
- [ ] config.toml configured for both PCs
- [ ] Test transfer completed successfully
- [ ] Received files verified to work correctly
- [ ] Firewall configured to allow port 5001
- [ ] Review SECURITY.md for security details

---

## 🗓️ Version History

### v2.0.0 (July 25, 2026)
- ✨ Path traversal protection
- ✨ Enhanced file type detection
- 🔧 Updated dependencies
- 📚 Comprehensive documentation
- 🐛 Bug fixes and improvements

### v1.0.0 (Original)
- Basic file transfer
- SHA256 verification
- Video/image filtering

---

## 🔗 Related Resources

- [Python Official Site](https://www.python.org/)
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [OWASP Security Guide](https://owasp.org/)
- [SHA256 Algorithm](https://en.wikipedia.org/wiki/SHA-2)

---

## 📅 Last Updated

July 25, 2026 | v2.0.0

---

**Ready to transfer safely?** Start with [QUICKSTART.md](QUICKSTART.md) 🚀
