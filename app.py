from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from facebook_video_downloader import FacebookVideoDownloader
from utils import is_valid_facebook_url, normalize_fb_url
import os

app = Flask(__name__)
# Configure CORS properly
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

downloader = FacebookVideoDownloader()

@app.route("/api/metadata", methods=["POST", "OPTIONS"])
def get_video_metadata():
    """Extract and return video metadata for preview"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        url = data.get("url")

        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Validate URL format
        if not is_valid_facebook_url(url):
            return jsonify({"error": "Invalid Facebook URL format"}), 400
        
        # Extract metadata
        metadata = downloader.extract_video_metadata(url)
        
        if not metadata:
            return jsonify({"error": "Failed to extract video metadata"}), 500
        
        # Return formatted metadata
        response_data = {
            "success": True,
            "metadata": {
                "title": metadata.get('title', 'Unknown Title'),
                "description": metadata.get('description', ''),
                "uploader": {
                    "name": metadata.get('uploader', 'Unknown User'),
                    "id": metadata.get('uploader_id', ''),
                    "url": metadata.get('uploader_url', ''),
                    "profile_pic": f"https://graph.facebook.com/{metadata.get('uploader_id', 'default')}/picture?type=large" if metadata.get('uploader_id') else ""
                },
                "stats": {
                    "views": metadata.get('view_count', 0),
                    "views_formatted": metadata.get('view_count_formatted', '0'),
                    "likes": metadata.get('like_count', 0),
                    "likes_formatted": metadata.get('like_count_formatted', '0'),
                    "comments": metadata.get('comment_count', 0),
                    "comments_formatted": metadata.get('comment_count_formatted', '0'),
                    "shares": metadata.get('repost_count', 0),
                    "shares_formatted": metadata.get('repost_count_formatted', '0')
                },
                "video_info": {
                    "duration": metadata.get('duration', 0),
                    "duration_formatted": metadata.get('duration_formatted', 'Unknown'),
                    "upload_date": metadata.get('upload_date', ''),
                    "upload_date_formatted": metadata.get('upload_date_formatted', 'Unknown'),
                    "thumbnail": metadata.get('thumbnail', ''),
                    "resolution": metadata.get('resolution', 'Unknown'),
                    "format": metadata.get('format', 'Unknown'),
                    "filesize": metadata.get('filesize', 0),
                    "fps": metadata.get('fps', 0)
                },
                "url_info": {
                    "original_url": url,
                    "normalized_url": normalize_fb_url(url),
                    "webpage_url": metadata.get('webpage_url', url),
                    "video_id": metadata.get('id', '')
                }
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Metadata extraction error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to extract metadata: {str(e)}"
        }), 500

@app.route("/api/download", methods=["POST", "OPTIONS"])
def download_video():
    """Download video endpoint"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        url = data.get("url")

        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Validate URL format
        if not is_valid_facebook_url(url):
            return jsonify({"error": "Invalid Facebook URL format"}), 400

        success = downloader.download_video(url)
        if success:
            # Get the latest file in download folder
            try:
                files = sorted(
                    [os.path.join(downloader.download_folder, f) for f in os.listdir(downloader.download_folder)],
                    key=os.path.getmtime,
                    reverse=True
                )
                latest_file = files[0] if files else None
                if latest_file:
                    # Also return metadata if available
                    metadata = downloader.last_extracted_info
                    response = {
                        "success": True,
                        "file": os.path.basename(latest_file),
                        "file_path": latest_file
                    }
                    
                    if metadata:
                        response["metadata"] = {
                            "title": metadata.get('title', 'Unknown'),
                            "uploader": metadata.get('uploader', 'Unknown'),
                            "duration_formatted": metadata.get('duration_formatted', 'Unknown')
                        }
                    
                    return jsonify(response)
            except Exception as e:
                print(f"File listing error: {e}")
        
        return jsonify({"success": False, "error": "Download failed"}), 500
        
    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({
            "success": False,
            "error": f"Download failed: {str(e)}"
        }), 500

@app.route("/api/files/<filename>", methods=["GET"])
def serve_file(filename):
    """Serve downloaded files"""
    try:
        return send_from_directory(downloader.download_folder, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Facebook Video Downloader API",
        "version": "2.0"
    })

@app.route("/api/validate-url", methods=["POST", "OPTIONS"])
def validate_url():
    """Validate Facebook URL format"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"valid": False, "error": "No JSON data provided"})
            
        url = data.get("url")
        
        if not url:
            return jsonify({"valid": False, "error": "No URL provided"})
        
        is_valid = is_valid_facebook_url(url)
        normalized_url = normalize_fb_url(url) if is_valid else url
        
        return jsonify({
            "valid": is_valid,
            "original_url": url,
            "normalized_url": normalized_url if is_valid else None,
            "supported_formats": [
                "https://www.facebook.com/watch/?v=...",
                "https://fb.watch/...",
                "https://www.facebook.com/share/v/...",
                "https://www.facebook.com/reel/..."
            ]
        })
        
    except Exception as e:
        return jsonify({
            "valid": False,
            "error": f"Validation failed: {str(e)}"
        })

if __name__ == "__main__":
    print("Starting Facebook Video Downloader API...")
    app.run(debug=True, port=5000, host='127.0.0.1')