# Safe Media Transfer - Setup & Usage Guide

## Overview

Safe Media Transfer is a secure file-sharing application designed to safely transfer videos and images between two PCs, especially when one PC may have malware or viruses.

### Key Security Features
- ✅ **Path Traversal Protection**: Prevents access to files outside the selected directory
- ✅ **SHA256 Integrity Verification**: Ensures files aren't corrupted or modified during transfer
- ✅ **File Type Validation**: Only allows approved image and video formats
- ✅ **Separate Transfer Workflows**: Videos and images are handled separately for additional safety
- ✅ **No Executable Files**: Blocks all executable and dangerous file types
- ✅ **Resume Capability**: Can safely resume interrupted transfers

---

## System Requirements

### Both Machines (Sender & Receiver)

   - Download from: https://www.python.org/downloads/
   - ⚠️ Check "Add Python to PATH" during installation

2. **Network Connection**
   - Direct USB/Ethernet cable connection, or
   - Local Area Network (LAN) connection
   - Network should be isolated/secure

3. **Storage Space**
   - Enough space for files being transferred
   - Additional 10% for temporary staging files

---

## Installation

### Step 1: Extract Files

1. Unzip `safe_media_transfer.zip` to your preferred location
2. Navigate to the extracted folder
3. Open Command Prompt/Terminal in this directory

### Step 2: Install Dependencies

Run this command on **BOTH** sender and receiver:

```bash
# Windows
pip install -r requirements.txt

# macOS/Linux
pip3 install -r requirements.txt
```

⏳ This may take 2-5 minutes the first time.

### Step 3: Verify Installation

Test that everything works:

```bash
# Windows
python -m pip list

# macOS/Linux
python3 -m pip list
```

You should see `PySide6` in the list.

---

## Configuration

### Edit `config.toml`

1. Open `config.toml` in a text editor (Notepad, VS Code, etc.)

2. **For the RECEIVER PC** (where you want to receive files):
   ```toml
   [app]
   mode = "receiver"
   
   [network]
   bind_ip = "0.0.0.0"        # Accept from any PC on network
   port = 5001                 # Can change if port 5001 is in use
   
   [storage]
   default_destination = "C:\\Transfers\\Inbox"  # Your receive folder
   ```

3. **For the SENDER PC** (with potential malware):
   ```toml
   [app]
   mode = "sender"
   
   [network]
   bind_ip = "127.0.0.1"       # Only local transfers
   receiver_ip = "192.168.1.5" # Put receiver's IP here
   port = 5001                 # Must match receiver's port
   ```

### Finding Your PC's IP Address

**Windows:**
```bash
ipconfig
```
Look for "IPv4 Address" (usually starts with 192.168 or 10.0)

**macOS/Linux:**
```bash
ifconfig
```

---

## Running the Application

### Method 1: From Terminal (Recommended)

**On RECEIVER PC:**
```bash
# Windows
python receiver_main.py

# macOS/Linux
python3 receiver_main.py
```

**On SENDER PC:**
```bash
# Windows
python sender_main.py

# macOS/Linux
python3 sender_main.py
```

### Method 2: Create Shortcuts

**Windows - Create `run_receiver.bat`:**
```batch
@echo off
cd /d "%~dp0"
python receiver_main.py
pause
```

**Windows - Create `run_sender.bat`:**
```batch
@echo off
cd /d "%~dp0"
python sender_main.py
pause
```

Save these files in the application directory and double-click to run.

---

## Using the Application

### Workflow

#### 1. Start Receiver (Destination PC)

1. Run the receiver application
2. You'll see: "Waiting for connection..."
3. Keep this window open

#### 2. Start Sender (Source PC with files)

1. Run the sender application
2. Click "Select Folder" button
3. Choose the folder containing your files
4. Wait for scan to complete

#### 3. Transfer Videos

1. The sender shows all detected videos
2. Select videos you want to transfer
3. Click "Send Videos" button
4. Wait for all videos to complete
5. Check log for transfer status

#### 4. Transfer Images

1. Select images you want to transfer
2. Click "Send Images" button  
3. Wait for all images to complete
4. Receiver PC will show progress

#### 5. Verify Transfer

- Receiver shows completion status
- Check `default_destination` folder for files
- Files are verified automatically during transfer

### File Selection

- ✅ **Can Select**: Video and image files
- ❌ **Cannot Select**: Executables, archives, scripts, documents
- ✅ **Supported Videos**: `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, etc.
- ✅ **Supported Images**: `.jpg`, `.png`, `.gif`, `.webp`, `.bmp`, etc.

---

## Network Setup Examples

### Example 1: USB Direct Cable (Most Secure)

```
PC A (Sender)    ←USB Cable→    PC B (Receiver)
Port 5001                       Port 5001
```

Both must be on same local network via USB adapter.

### Example 2: Ethernet Network

```
PC A (Sender) --→ Network Switch ←-- PC B (Receiver)
192.168.1.10                        192.168.1.20
Port 5001                           Port 5001
```

### Example 3: Isolated LAN (Safest)

```
PC A (Sender) --→ Isolated Switch ←-- PC B (Receiver)
10.0.0.2                            10.0.0.3
Port 5001                           Port 5001
```

**Never expose this application to the internet.**

---

## Configuration Details

### `config.toml` Reference

```toml
[app]
name = "Safe Media Transfer"
mode = "receiver"  # or "sender"
debug_logging = false  # Set to true only for troubleshooting

[network]
bind_ip = "0.0.0.0"  # Receiver: accept all connections
receiver_ip = "192.168.1.5"  # Sender: receiver's IP
port = 5001  # Connection port (both must match)
connect_timeout_seconds = 10
read_timeout_seconds = 30
write_timeout_seconds = 30

[transfer]
chunk_size_bytes = 4194304  # 4MB chunks (don't change)
resume_enabled = true  # Resume interrupted transfers
max_file_size_bytes = 1099511627776  # 1TB limit
duplicate_policy = "replace"  # replace/skip/fail

[storage]
default_destination = "C:\\Transfers"  # Receiver's save location

[security]
path_validation_enabled = true  # Prevent directory escape
block_symlinks = true  # Block symbolic link attacks
verify_file_boundaries = true  # Verify files stay in directory
```

---

## Troubleshooting

### "Connection Refused"

1. Check receiver is running (no errors in terminal)
2. Verify firewall isn't blocking port 5001
3. Confirm IP address is correct in sender's config
4. Check both PCs are on same network

**Fix:**
```bash
# Windows: Check if port is in use
netstat -ano | findstr :5001

# Allow through firewall
netsh advfirewall firewall add rule name="Safe Media Transfer" dir=in action=allow protocol=tcp localport=5001
```

### "File Type Not Supported"

- The file extension isn't in the allowed list
- Check `config.toml` `[allowed_extensions]` section
- Add extension if you trust it (be careful!)

### "Transfer Stalled or Stuck"

1. Check network connection is stable
2. Verify disk space on receiver
3. Check logs in `logs/` folder
4. Restart both applications

### Application Won't Start

1. Verify Python is installed: `python --version`
2. Verify dependencies: `pip list`
3. Reinstall if needed: `pip install -r requirements.txt --force-reinstall`
4. Check logs in `logs/receiver.log` or `logs/sender.log`

### Slow Transfer Speed

**Normal speeds:**
- USB 3.0+: 100-400 MB/s
- Gigabit Ethernet: 100-125 MB/s
- WiFi: 20-50 MB/s

**Optimize:**
1. Use wired connection (Ethernet/USB) instead of WiFi
2. Close other applications
3. Ensure both PCs have sufficient RAM
4. Move to less congested network

---

## Security Considerations

### Best Practices

1. ✅ **Always use wired connection** (USB/Ethernet, not WiFi)
2. ✅ **Keep application on isolated network** (not connected to internet)
3. ✅ **Verify file list** before transferring
4. ✅ **Check file destinations** after transfer
5. ✅ **Close ports after use** if on accessible network
6. ✅ **Enable firewall** on both PCs
7. ✅ **Keep PCs updated** with latest security patches

### What This App Does NOT Do

- ❌ Does NOT encrypt network traffic (assume untrusted network)
- ❌ Does NOT scan files for malware (only checks file types)
- ❌ Does NOT authenticate users (anyone on network can connect)

### If One PC Has Malware

- ✅ Malware cannot access files in other directories
- ✅ Malware cannot send executable files
- ✅ All transfers are verified for integrity
- ⚠️ Malware on sender might still see file names being transferred

---

## Log Files

Logs are saved in the `logs/` folder:

- `sender.log` - Sender application logs
- `receiver.log` - Receiver application logs

**View logs to debug issues:**

```bash
# Windows
type logs\receiver.log

# macOS/Linux
cat logs/receiver.log
```

### Enable Debug Logging

In `config.toml`:
```toml
[app]
debug_logging = true
```

This creates much more detailed logs but also creates larger files.

---

## Advanced: Custom Allowed Extensions

To add support for additional file formats:

1. Edit `config.toml`
2. Find `[allowed_extensions.images]` or `[allowed_extensions.videos]`
3. Add your extension in lowercase (e.g., `.webp`)

Example:
```toml
[allowed_extensions.images]
values = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".heic", ".cr2"]
```

⚠️ **Only add extensions you trust!**

---

## Performance Tips

### For Large Files (>2GB)

1. Use USB 3.0 or Gigabit Ethernet
2. Ensure at least 10GB free disk space
3. Close other applications
4. Transfer one file at a time
5. Don't interrupt transfers (let them complete)

### For Many Small Files

1. Reduce `chunk_size_bytes` if network is unstable
2. Increase `max_file_count` if you have many files
3. Disable resume if network is stable: `resume_enabled = false`

---

## Uninstallation

1. Delete the application folder
2. Optional: Uninstall Python if you don't need it

```bash
pip uninstall PySide6 pydantic cryptography python-magic-bin python-dotenv
```

---

## Support & Issues

### Reporting Problems

1. Collect logs from `logs/` folder
2. Note the exact error message
3. Describe when it happened
4. List your network setup

### Check Logs For

- `ERROR` - Problems that need fixing
- `WARNING` - Unusual situations
- `INFO` - Normal operation details

---

## Version History

- **v2.0.0** (July 2026) - Security enhancements, path validation, improved config
- **v1.0.0** - Initial release

---

## License

This application is provided as-is for secure file transfers.

---

**Last Updated:** July 25, 2026

For the latest updates and documentation, check the README.md file.
