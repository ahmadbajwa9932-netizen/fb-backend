import subprocess
import sys

def auto_update_ytdlp():
    """
    Automatically update yt-dlp to the latest version.
    Runs only when the program starts.
    """
    try:
        print("🔄 Checking for yt-dlp updates...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
        print("✅ yt-dlp is up to date.")
    except Exception as e:
        print(f"⚠️ Auto-update failed: {e}")
