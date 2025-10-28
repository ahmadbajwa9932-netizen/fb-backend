from updater import auto_update_ytdlp

# Run auto-update before anything else
auto_update_ytdlp()

import sys
import os
from facebook_video_downloader import FacebookVideoDownloader
from utils import is_valid_facebook_url, normalize_fb_url  # ⬅️ added normalize_fb_url

def print_banner():
    """Print application banner"""
    print("="*60)
    print("📥 Facebook Video Downloader v2.0")
    print("="*60)
    print("Features:")
    print("• Download Facebook videos, reels, and stories")
    print("• Automatic retry on failures")
    print("• Smart filename handling")
    print("• Network error recovery")
    print("="*60)

def print_help():
    """Print help information"""
    print("\n📖 Help:")
    print("• Supported URLs:")
    print("  - https://www.facebook.com/watch/?v=...")
    print("  - https://fb.watch/...")
    print("  - https://www.facebook.com/share/v/...")
    print("  - https://www.facebook.com/reel/...")
    print("• Type 'help' for this help message")
    print("• Type 'test' to test connection")
    print("• Type 'exit' or 'quit' to exit")

def main():
    print_banner()
    
    # Initialize downloader
    try:
        downloader = FacebookVideoDownloader()
    except Exception as e:
        print(f"❌ Failed to initialize downloader: {e}")
        sys.exit(1)
    
    print(f"📁 Download folder: {os.path.abspath(downloader.download_folder)}")
    print("\nReady to download! Type 'help' for usage information.")
    
    while True:
        try:
            video_url = input("\n🔗 Enter Facebook video URL: ").strip()
            
            # Handle special commands
            if video_url.lower() in ['exit', 'quit', 'q']:
                print("👋 Thanks for using Facebook Video Downloader!")
                break
            elif video_url.lower() == 'help':
                print_help()
                continue
            elif video_url.lower() == 'test':
                print("🔍 Testing connection to Facebook...")
                if downloader.check_connection():
                    print("✅ Connection successful!")
                else:
                    print("❌ Connection failed. Check your internet connection.")
                continue
            elif not video_url:
                print("⚠️  Please enter a valid URL.")
                continue
            
            # Validate URL format
            if not is_valid_facebook_url(video_url):
                print("⚠️  Invalid Facebook URL format.")
                print("   Please use a valid Facebook video URL (fb.watch, facebook.com/watch, etc.)")
                continue
            
            # Normalize URL before downloading
            video_url = normalize_fb_url(video_url)

            # Attempt download
            print(f"\n🎯 Processing: {video_url}")
            success = downloader.download_video(video_url)
            
            if success:
                print("🎉 Download completed successfully!")
            else:
                print("💥 Download failed. Please try again or check the URL.")
                
            # Ask if user wants to continue
            print("\n" + "-"*50)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Download interrupted by user.")
            continue
        except EOFError:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)
