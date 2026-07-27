# Quick Start Guide - 5 Minutes to First Transfer

## What You Need

- Two PCs on same network (or connected via USB adapter)
- Python 3.9+ installed on both
- This application folder on both PCs

## Install (2 minutes)

**On BOTH PCs:**

1. Open Terminal/Command Prompt in the application folder
2. Run: `pip install -r requirements.txt`

That's it! Wait for it to finish.

---

## Setup (2 minutes)

### RECEIVER PC (Destination)

Edit `config.toml`:

```toml
[app]
mode = "receiver"

[storage]
default_destination = "C:\\MyTransfers"
```

Save and close.

### SENDER PC (Source)

1. Find RECEIVER's IP address:
   - Windows: Open Command Prompt, type `ipconfig`, look for IPv4 Address (like 192.168.1.5)

2. Edit `config.toml`:

```toml
[app]
mode = "sender"

[network]
receiver_ip = "192.168.1.5"  # PUT RECEIVER'S IP HERE
```

Save and close.

---

## Run (1 minute)

### Step 1: Start RECEIVER (Do this first!)

```bash
python receiver_main.py
```

You should see: **"Waiting for incoming connection..."**

Leave this window open.

### Step 2: Start SENDER

```bash
python sender_main.py
```

A window will appear with buttons.

---

## Transfer Files

### In the SENDER window:

1. Click **"Select Folder"**
2. Browse to your folder with videos/images
3. Click **"Open"**
   - Wait for folder scan to complete
   - Application lists all safe files

### Transfer Videos:

1. Check the boxes next to videos you want
2. Click **"Send Videos"**
3. Wait for all to complete ✅

### Transfer Images:

1. Check the boxes next to images you want
2. Click **"Send Images"**
3. Wait for all to complete ✅

### Check RECEIVER PC:

- Open the `default_destination` folder
- Your files are there! ✅

---

## Done!

That's it! Your files are transferred and verified.

### What Just Happened:

✅ Only videos and images were transferred
✅ No executables or dangerous files were sent
✅ File integrity was verified (SHA256)
✅ Files were checked to prevent escaping the directory
✅ Everything is logged for your records

---

## Troubleshooting in 30 Seconds

### "Connection refused"
- Make sure RECEIVER window is still open
- Check RECEIVER PC is on and awake
- Verify receiver_ip is correct in config.toml

### "File type not supported"
- Only images and videos are supported
- Use an image viewer to convert unsupported formats
- File must have proper extension

### "Transfer stuck or slow"
- Network might be congested
- Try smaller batch (5-10 files at a time)
- Use wired Ethernet instead of WiFi

### "Hash mismatch error"
- Network error occurred
- File is safe - not transferred
- Try again, it will resume from where it stopped

---

## Security Tips

1. ✅ Use wired connection (Ethernet cable or USB)
2. ✅ Keep both PCs on same private network
3. ✅ Don't expose to internet
4. ✅ Close application when done
5. ✅ Check received files before using

---

## What's Blocked?

❌ .exe, .dll, .bat, .cmd (executables)
❌ .zip, .rar, .7z (archives)
❌ .py, .js, .sh (scripts)
❌ Any file outside selected directory

✅ .mp4, .avi, .mkv, .mov (videos)
✅ .jpg, .png, .gif, .webp (images)
✅ All files in selected directory only

---

## Next Steps

For more information:
- **Setup Guide**: See `SETUP_GUIDE.md`
- **Security Details**: See `SECURITY.md`
- **Troubleshooting**: See bottom of `SETUP_GUIDE.md`

---

**Time to first transfer: ~5 minutes** ⏱️
