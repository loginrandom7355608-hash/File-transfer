# Safe Media Transfer - Security Implementation

## Executive Summary

This document outlines the security measures implemented in Safe Media Transfer to protect against malware, data theft, and system compromise during file transfers.

---

## Threat Model

### Assumed Threats

1. **Malware on Sender PC**
   - May attempt to intercept or modify files
   - May try to access files outside selected directory
   - May scan network for vulnerabilities

2. **Network Eavesdropping** (if on shared network)
   - Attacker can see file names and sizes
   - Attacker can see transfer progress
   - Attacker cannot modify file contents (SHA256 verification)

3. **Supply Chain Attacks**
   - Malicious file substitution before transfer
   - Filesystem inconsistencies during transfer

### Out of Scope

- Attacks on Python interpreter
- Attacks on operating system
- Physical theft of hardware
- Quantum computing attacks
- Attacks requiring administrative access

---

## Security Controls

### 1. Path Traversal Prevention

**Problem:** Malicious code could use paths like `../../../Windows/System32` to access system files.

**Solution:**
```python
class PathSecurityValidator:
    def validate_for_destination(self, relative_path):
        # 1. Normalize path (remove ../,  ./ patterns)
        # 2. Resolve to absolute path
        # 3. Verify it's still within allowed root
        # 4. Reject if outside boundaries
```

**Implementation Details:**
- All incoming paths are validated before use
- Symbolic links are detected and optionally blocked
- Path traversal attempts are logged

**Testing:**
```python
# These will be REJECTED:
../../../windows/system32/drivers
....//....//....//windows
/etc/passwd
C:\\Windows\\System32
```

### 2. File Type Validation

**Problem:** Executables and scripts could install malware.

**Solution:**
```toml
[allowed_extensions.images]
values = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"]

[allowed_extensions.videos]
values = [".mp4", ".mkv", ".mov", ".avi", ".webm"]

[blocked_extensions]
values = [
    ".exe", ".dll", ".bat", ".cmd",
    ".ps1", ".sh", ".py", ".js", ".jar",
    ".zip", ".rar", ".7z", ".iso"
]
```

**Defense Layers:**
1. Whitelist of allowed extensions
2. Blacklist of dangerous extensions
3. MIME type verification via `python-magic`
4. Header inspection for file type spoofing

**Example Attack Blocked:**
```
malware.exe → renamed → malware.mp4
❌ BLOCKED: Header/magic bytes show it's PE executable, not video
```

### 3. Integrity Verification

**Problem:** Malware could corrupt files during transfer.

**Solution:** SHA256 hashing on both sender and receiver

**Process:**
```
Sender:
1. Read file → SHA256 hash (computed while reading)
2. Send file chunks
3. Send final hash to receiver

Receiver:
1. Receive file chunks
2. Save to temporary .part file
3. Compute SHA256 of received file
4. Compare with sender's hash
5. If mismatch: abort and log error
6. If match: move .part to final location
```

**Security Properties:**
- Detects accidental corruption (network errors)
- Detects intentional modification
- Uses cryptographically secure algorithm (SHA256)
- Cannot be forged without collision (computationally infeasible)

**Example:**
```
File: video.mp4
Sender SHA256: a4d2c8...f9e2
Receiver SHA256: a4d2c8...f9e2 ✅ Match - transfer verified

If malware modifies: 
Receiver SHA256: b8f3a9...a1c4 ❌ Mismatch - transfer rejected
```

### 4. Transfer Protocol Security

**Problem:** Attacker could inject malicious messages or disrupt transfers.

**Solution:** Strict message protocol with validation

**Protocol Flow:**
```
1. HELLO → HELLO_ACK (handshake verification)
2. MANIFEST → MANIFEST_RESULT (file list verification)
3. FILE_START → FILE_RESUME_INFO (per-file protocol)
4. [BINARY CHUNKS] (actual file data)
5. FILE_COMPLETE → FILE_HASH_RESULT (integrity check)
6. TRANSFER_COMPLETE → TRANSFER_COMPLETE_ACK (cleanup)
```

**Protection:**
- Strict type checking on messages
- Expected response validation
- Timeout protection
- Error handling for protocol violations

### 5. Staged File Writing

**Problem:** Incomplete or corrupted transfers could leave unusable files.

**Solution:** Write to temporary `.part` file until complete

**Process:**
```
Receiving:
1. Save to: `filename.mp4.part` (staging file)
2. Verify integrity on staging file
3. On success: rename to `filename.mp4`
4. On failure: delete staging file (can be resumed later)

Benefits:
✅ Incomplete transfers don't overwrite complete files
✅ Can resume from last known good state
✅ Atomic rename operation
✅ Clean error recovery
```

### 6. Network Access Control

**Problem:** Unauthorized PCs could connect and access/send files.

**Solution:** Local-only configuration by default

```toml
[network]
# Receiver (destination):
bind_ip = "0.0.0.0"  # Accept from any IP on local network

# Sender (source):
bind_ip = "127.0.0.1"  # Local-only (can't receive connections)

# Both must agree on port:
port = 5001
```

**Security Model:**
- No authentication (assumes trusted network)
- Firewall rules should restrict port access
- No encryption (assumes isolated/private network)
- IPv4 and IPv6 supported

### 7. Logging & Audit Trail

**Problem:** Can't detect or investigate security incidents.

**Solution:** Comprehensive logging of all operations

**Logged Events:**
```
✓ Application startup
✓ Configuration loading
✓ Connection attempts
✓ File scan results
✓ File transfers (sent/received)
✓ Hash mismatches
✓ Errors and warnings
✓ Security violations
```

**Example Log Entry:**
```
2026-07-25 14:32:15 [INFO] FileScanner: Starting scan of /Users/john/Videos
2026-07-25 14:32:18 [INFO] FileScanner: Found 15 video files
2026-07-25 14:32:20 [WARNING] FileScanner: Skipped malware.exe (blocked_extension)
2026-07-25 14:32:25 [INFO] SenderService: Connecting to 192.168.1.5:5001
2026-07-25 14:32:26 [INFO] SenderService: Connected, sending manifest
2026-07-25 14:32:30 [INFO] FileTransfer: Sending video1.mp4 (size: 1.2GB)
2026-07-25 14:34:45 [INFO] FileTransfer: video1.mp4 transfer complete (hash verified)
2026-07-25 14:36:00 [ERROR] PathValidator: Invalid path received: ../../../system32
```

### 8. Configuration Security

**Problem:** Insecure defaults could leave system vulnerable.

**Solution:** Secure defaults with configuration validation

```toml
# Receiver destination must be valid
[storage]
default_destination = "C:\\Transfers"  # Must exist or be creatable

# File extensions strictly configured
[allowed_extensions.images]
values = [".jpg", ".jpeg", ".png"]  # Exact match required

[blocked_extensions]
values = [".exe", ".dll", ".sys"]  # Blocks all executables

# Security features cannot be disabled
[security]
path_validation_enabled = true  # Always true, can't change
block_symlinks = true
verify_file_boundaries = true
```

**Validation:**
- Config file is validated on startup
- Invalid paths are rejected
- Missing required values use secure defaults
- Configuration errors are logged

---

## Data Security

### At Rest (Stored Files)

- Files are stored with OS filesystem permissions
- Temporary `.part` files are in same directory
- No additional encryption applied
- **Responsibility**: User must secure the storage location

### In Transit (Network)

- **No encryption** by default (assume private network)
- SHA256 integrity verification prevents tampering
- File type validation prevents executable injection
- **Recommendation**: Use IPsec or VPN for untrusted networks

### In Memory

- File contents are never fully loaded (streaming chunks)
- Maximum chunk size: 4MB (configurable)
- No plaintext passwords or secrets stored
- Standard OS memory protections apply

---

## Cryptographic Standards

### Hashing Algorithm

- **Algorithm**: SHA256 (256-bit)
- **Standard**: FIPS 180-4
- **Library**: Python standard library `hashlib`
- **Collision Resistance**: 2^128 computational difficulty
- **Usage**: File integrity verification

### Why SHA256?

✅ Cryptographically secure
✅ Fast enough for large files
✅ Not compromised (unlike MD5, SHA1)
✅ Available everywhere (standard library)
❌ Does NOT require key material (not authentication)

### What It Protects Against

✅ Network transmission errors
✅ Storage corruption
✅ Accidental file modifications
✅ Some intentional file modifications (if attacker doesn't know hash beforehand)

### What It Does NOT Protect Against

❌ Attacker who controls sender (can pre-compute correct hash)
❌ Attacker with ability to modify file AND hash simultaneously
❌ Future quantum computers (in theory, far future)

---

## Testing & Verification

### Path Traversal Tests

```python
# These test cases should all fail:
validator.validate_for_destination("../../../windows")  # ❌
validator.validate_for_destination("..\\..\\system32")  # ❌
validator.validate_for_destination("/etc/passwd")       # ❌
validator.validate_for_destination("...//...//...")     # ❌

# These should succeed:
validator.validate_for_destination("subfolder/video.mp4")  # ✅
validator.validate_for_destination("2024/08/photo.jpg")    # ✅
```

### File Type Tests

```python
# Malware disguised as video:
magic.mime_type("malware.mp4")  # Returns "application/x-dosexec"
# Action: REJECT (actual type is executable, not video)

# Legitimate video:
magic.mime_type("video.mp4")  # Returns "video/mp4"
# Action: ACCEPT
```

### Hash Integrity Tests

```python
# Sender computes:
hash_sent = sha256_file("video.mp4")  # "a4d2c8...f9e2"

# Network error corrupts 1 byte during transfer
# Receiver computes:
hash_received = sha256_file("video.mp4.part")  # "b8f3a9...a1c4"

# Verification:
if hash_sent == hash_received:  # ❌ False
    move to final location
else:
    reject and delete staging file  # ✅ Correct behavior
```

---

## Known Limitations

### What This Application CAN Do

✅ Safely transfer videos and images
✅ Prevent access to files outside selected directory
✅ Verify file integrity during transfer
✅ Block execution of malicious file types
✅ Create audit trails of all transfers
✅ Resume interrupted transfers safely

### What This Application CANNOT Do

❌ Scan files for malware (would require antivirus engine)
❌ Encrypt network traffic (would require TLS/SSL)
❌ Authenticate users (no user accounts/passwords)
❌ Protect against OS-level compromise
❌ Protect against MITM attacks (no encryption)
❌ Guarantee security against 0-day exploits

### Recommended Additional Measures

1. **Network Security**
   - Use isolated LAN (not connected to internet)
   - Use wired Ethernet (not WiFi) for better isolation
   - Enable firewall on both PCs
   - Restrict port 5001 to trusted IPs

2. **Malware Prevention**
   - Run Windows Defender or equivalent antivirus
   - Keep OS updated with latest patches
   - Don't download files from untrusted sources
   - Use sandboxing if available

3. **Transfer Verification**
   - Visually inspect file list before transferring
   - Check file sizes are as expected
   - Verify received files play/open correctly
   - Delete suspicious files

4. **System Hardening**
   - Disable autorun features
   - Disable execution of scripts in common folders
   - Use security software with file monitoring
   - Consider using live boot OS (Linux USB) for infected PCs

---

## Security Updates

### Version 2.0.0 (July 2026)

**New Security Features:**
- ✅ Path traversal prevention (PathSecurityValidator)
- ✅ Enhanced file type detection (python-magic-bin)
- ✅ Improved logging and audit trails
- ✅ Configuration validation
- ✅ Better error handling

**Deprecated:**
- Removed insecure features from v1.0

**Recommendations:**
- Upgrade from v1.0 immediately
- Update requirements.txt
- Review configuration settings
- Check logs for any issues

---

## Security Incident Response

### If Transfer Fails With Hash Mismatch

**Automatic Actions Taken:**
1. Staging file (.part) is preserved
2. Error is logged with timestamp
3. Transfer can be resumed

**Manual Investigation:**
```bash
# Check logs for details
cat logs/receiver.log | grep "HASH_RESULT"

# File is safe - receiver didn't accept corrupted file
# Try transfer again
```

### If Path Validation Fails

**Automatic Actions Taken:**
1. File is rejected
2. Error is logged
3. Transfer continues with next file

**Manual Investigation:**
```bash
# Check what path was rejected
cat logs/receiver.log | grep "Invalid path"

# Verify no malicious paths were attempted
# This might indicate:
# - Sender misconfiguration
# - Malware attempting path traversal
```

### If Blocked Extension is Detected

**Automatic Actions Taken:**
1. File is skipped
2. Warning is logged
3. Transfer continues

**Manual Investigation:**
```bash
# Check what was blocked
cat logs/sender.log | grep "blocked_extension"

# If legitimate file type:
# - Add to allowed_extensions in config.toml
# - Restart application
# - Re-transfer the file
```

---

## Compliance & Standards

### OWASP Top 10 Coverage

| Vulnerability | Coverage | Method |
|---|---|---|
| Path Traversal | ✅ Full | PathSecurityValidator |
| Command Injection | ✅ Full | No shell execution |
| Arbitrary File Upload | ✅ Full | Extension/type checks |
| Unvalidated Redirects | ✅ Full | No redirects |
| Security Misconfiguration | ✅ Full | Secure defaults |
| Missing Encryption | ⚠️ Partial | User's responsibility |
| Broken Authentication | ⚠️ N/A | Network-level trust |
| XXE Injection | ✅ Full | No XML parsing |
| CSRF | ✅ Full | No web interface |
| Broken Access Control | ✅ Full | Directory boundary checks |

### CWE (Common Weakness Enumeration)

| CWE | Title | Status |
|---|---|---|
| CWE-22 | Path Traversal | ✅ Mitigated |
| CWE-434 | Unrestricted Upload | ✅ Mitigated |
| CWE-200 | Information Exposure | ✅ Mitigated |
| CWE-295 | Improper Certificate Validation | ⚠️ N/A (no HTTPS) |
| CWE-352 | Cross-Site Request Forgery | ✅ N/A |

---

## Appendix: Security Checklist

Before using Safe Media Transfer:

- [ ] Both PCs are on isolated, trusted network
- [ ] Port 5001 is not exposed to internet
- [ ] Firewall is enabled on both PCs
- [ ] OS and applications are up to date
- [ ] Antivirus/antimalware is running
- [ ] Python and dependencies are installed
- [ ] `config.toml` has been reviewed and updated
- [ ] Sender and receiver are configured correctly
- [ ] Test transfer works before transferring important files
- [ ] Received files are verified before using

---

## Contact & Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** publicly disclose the issue
2. **Do NOT** transfer sensitive files while vulnerability exists
3. Provide detailed steps to reproduce
4. Include the application version
5. Allow time for patches before public disclosure

---

**Last Updated:** July 25, 2026
**Version:** 2.0.0
