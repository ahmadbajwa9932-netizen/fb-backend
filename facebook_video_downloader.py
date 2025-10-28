import os
import time
import random
import uuid
from yt_dlp import YoutubeDL
from utils import sanitize_title, normalize_fb_url

class FacebookVideoDownloader:
    def __init__(self):
        self.download_folder = "Downloads"
        os.makedirs(self.download_folder, exist_ok=True)
        self.max_retries = 3
        self.retry_delay = 2
        self.last_extracted_info = None  # Store metadata for API access

    def extract_video_metadata(self, video_url):
        """
        Extract video metadata without downloading the video.
        Returns dict with video information like title, uploader, view count, etc.
        """
        video_url = normalize_fb_url(video_url)
        
        try:
            print("🔍 Extracting video metadata...")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writethumbnail': False,
                'writeinfojson': False,
                'socket_timeout': 30,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip,deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
            }

            with YoutubeDL(ydl_opts) as ydl:
                try:
                    info_dict = ydl.extract_info(video_url, download=False)
                    
                    if not info_dict:
                        return None
                    
                    # Helper function to safely get numeric values
                    def safe_get_number(value, default=0):
                        if value is None:
                            return default
                        try:
                            return int(float(value))
                        except (ValueError, TypeError):
                            return default
                    
                    # Extract and format metadata with safe handling
                    metadata = {
                        'title': info_dict.get('title', 'Unknown Title'),
                        'description': info_dict.get('description', ''),
                        'uploader': info_dict.get('uploader', 'Unknown User'),
                        'uploader_id': info_dict.get('uploader_id', ''),
                        'uploader_url': info_dict.get('uploader_url', ''),
                        'upload_date': info_dict.get('upload_date', ''),
                        'duration': safe_get_number(info_dict.get('duration')),
                        'view_count': safe_get_number(info_dict.get('view_count')),
                        'like_count': safe_get_number(info_dict.get('like_count')),
                        'comment_count': safe_get_number(info_dict.get('comment_count')),
                        'repost_count': safe_get_number(info_dict.get('repost_count')),  # shares
                        'thumbnail': info_dict.get('thumbnail', ''),
                        'webpage_url': info_dict.get('webpage_url', video_url),
                        'id': info_dict.get('id', ''),
                        'ext': info_dict.get('ext', 'mp4'),
                        'filesize': safe_get_number(info_dict.get('filesize')),
                        'format': info_dict.get('format', 'Unknown'),
                        'resolution': info_dict.get('resolution', 'Unknown'),
                        'fps': safe_get_number(info_dict.get('fps')),
                        'availability': info_dict.get('availability', 'unknown'),
                    }
                    
                    # Format duration to readable format
                    if metadata['duration']:
                        minutes, seconds = divmod(metadata['duration'], 60)
                        hours, minutes = divmod(minutes, 60)
                        if hours:
                            metadata['duration_formatted'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        else:
                            metadata['duration_formatted'] = f"{minutes:02d}:{seconds:02d}"
                    else:
                        metadata['duration_formatted'] = "Unknown"
                    
                    # Format numbers with commas
                    metadata['view_count_formatted'] = self.format_number(metadata['view_count'])
                    metadata['like_count_formatted'] = self.format_number(metadata['like_count'])
                    metadata['comment_count_formatted'] = self.format_number(metadata['comment_count'])
                    metadata['repost_count_formatted'] = self.format_number(metadata['repost_count'])
                    
                    # Format upload date
                    if metadata['upload_date']:
                        try:
                            from datetime import datetime
                            date_obj = datetime.strptime(metadata['upload_date'], '%Y%m%d')
                            metadata['upload_date_formatted'] = date_obj.strftime('%B %d, %Y')
                        except Exception as e:
                            print(f"Date formatting error: {e}")
                            metadata['upload_date_formatted'] = metadata['upload_date']
                    else:
                        metadata['upload_date_formatted'] = "Unknown"
                    
                    # Store for later use
                    self.last_extracted_info = metadata
                    
                    print("✅ Metadata extracted successfully!")
                    print(f"Title: {metadata['title']}")
                    print(f"Views: {metadata['view_count_formatted']}")
                    print(f"Duration: {metadata['duration_formatted']}")
                    
                    return metadata
                    
                except Exception as e:
                    print(f"❌ Failed to extract metadata: {e}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error during metadata extraction: {e}")
            return None

    def format_number(self, num):
        """Format numbers with K, M, B suffixes"""
        if not num or num == 0:
            return "0"
        
        try:
            # Convert to int first to handle float values
            num = int(float(num))
            if num >= 1_000_000_000:
                return f"{num / 1_000_000_000:.1f}B"
            elif num >= 1_000_000:
                return f"{num / 1_000_000:.1f}M"
            elif num >= 1_000:
                return f"{num / 1_000:.1f}K"
            else:
                return f"{num:,}"
        except (ValueError, TypeError):
            return str(num) if num else "0"

    def download_video(self, video_url):
        """
        Download Facebook video using yt-dlp with retry logic and better error handling.
        """
        # Normalize messy URLs before processing
        video_url = normalize_fb_url(video_url)

        for attempt in range(self.max_retries):
            try:
                print(f"⬇️ Starting download (Attempt {attempt + 1}/{self.max_retries}) for: {video_url}")
                
                # Generate unique temp filename to avoid conflicts
                unique_id = str(uuid.uuid4())[:8]
                temp_name = f'temp_{unique_id}.%(ext)s'
                
                # Enhanced yt-dlp options
                ydl_opts = {
                    'outtmpl': os.path.join(self.download_folder, temp_name),
                    'format': 'best[height<=720]/best',  # Prefer 720p or lower for stability
                    'noplaylist': True,
                    'quiet': False,
                    'no_warnings': False,
                    'extract_flat': False,
                    'writethumbnail': False,
                    'writeinfojson': False,
                    'ignoreerrors': False,
                    # Network options
                    'socket_timeout': 30,
                    'retries': 3,
                    'fragment_retries': 3,
                    'skip_unavailable_fragments': True,
                    # Headers to avoid detection
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-us,en;q=0.5',
                        'Accept-Encoding': 'gzip,deflate',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    },
                    # Progress hook
                    'progress_hooks': [self.progress_hook],
                }

                with YoutubeDL(ydl_opts) as ydl:
                    # Extract info first without downloading
                    print("🔍 Extracting video information...")
                    try:
                        info_dict = ydl.extract_info(video_url, download=False)
                    except Exception:
                        print("⚠️ Extractor failed, falling back to generic...")
                        ydl.params['force_generic_extractor'] = True
                        info_dict = ydl.extract_info(video_url, download=False)
                    
                    if not info_dict:
                        raise Exception("Could not extract video information")
                    
                    title = info_dict.get('title', f'video_{int(time.time())}')
                    ext = info_dict.get('ext', 'mp4')
                    
                    # Check if video is available
                    if info_dict.get('availability') == 'private':
                        raise Exception("This video is private or not accessible")
                    
                    # Create safe filename
                    safe_title = sanitize_title(title)
                    if not safe_title or safe_title.isspace():
                        safe_title = f'facebook_video_{int(time.time())}'
                    
                    final_filename = f"{safe_title}.{ext}"
                    final_path = os.path.join(self.download_folder, final_filename)
                    
                    # Check if file already exists
                    if os.path.exists(final_path):
                        counter = 1
                        while os.path.exists(final_path):
                            name_part = f"{safe_title}_{counter}.{ext}"
                            final_path = os.path.join(self.download_folder, name_part)
                            counter += 1
                    
                    # Now download the video
                    print("📥 Starting download...")
                    ydl.download([video_url])
                    
                    # Find the downloaded temp file
                    temp_pattern = f'temp_{unique_id}'
                    downloaded_file = None
                    
                    for file in os.listdir(self.download_folder):
                        if file.startswith(temp_pattern):
                            downloaded_file = os.path.join(self.download_folder, file)
                            break
                    
                    if downloaded_file and os.path.exists(downloaded_file):
                        # Rename to final filename
                        try:
                            os.rename(downloaded_file, final_path)
                            print(f"✅ Video downloaded successfully: {final_path}")
                            return True
                        except OSError as e:
                            print(f"⚠️ Warning: Could not rename file: {e}")
                            print(f"✅ Video downloaded as: {downloaded_file}")
                            return True
                    else:
                        raise Exception("Downloaded file not found")

            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for specific error types
                if 'failed to resolve' in error_msg or 'getaddrinfo failed' in error_msg:
                    print(f"🌐 Network error (DNS resolution failed) - Attempt {attempt + 1}")
                elif 'read timed out' in error_msg or 'timeout' in error_msg:
                    print(f"⏱️ Connection timeout - Attempt {attempt + 1}")
                elif 'cannot parse data' in error_msg:
                    print(f"🔧 Facebook structure changed - Attempt {attempt + 1}")
                elif 'private' in error_msg or 'not accessible' in error_msg:
                    print(f"🔒 Video is private or not accessible")
                    return False
                else:
                    print(f"❌ Error (Attempt {attempt + 1}): {e}")
                
                # If this is not the last attempt, wait and retry
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1) + random.uniform(1, 3)
                    print(f"⏳ Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed after {self.max_retries} attempts: {e}")
                    return False

        return False

    @staticmethod
    def progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = downloaded / total * 100
                speed = d.get('speed', 0)
                if speed:
                    speed_str = f" at {speed/1024:.1f}KB/s"
                else:
                    speed_str = ""
                print(f"\rDownloading... {percent:.1f}% completed{speed_str}", end='', flush=True)
            else:
                print(f"\rDownloading... {downloaded/1024:.1f}KB downloaded", end='', flush=True)
        elif d['status'] == 'finished':
            print(f"\n✓ Download completed: {d.get('filename', 'Unknown')}")

    def check_connection(self):
        """Check if we can connect to Facebook"""
        try:
            import requests
            response = requests.get('https://www.facebook.com', timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            return response.status_code == 200
        except:
            return False