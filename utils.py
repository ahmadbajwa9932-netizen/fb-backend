import re

def sanitize_title(title: str) -> str:
    """
    Clean up video titles so they are safe for filenames.
    - Removes emojis and special characters
    - Replaces spaces with underscores
    - Trims very long titles
    """
    # Remove unsafe characters
    safe = re.sub(r'[\\/*?:"<>|]', "", title)
    # Remove emojis and other non-ASCII chars
    safe = safe.encode("ascii", "ignore").decode("ascii")
    # Replace spaces with underscores
    safe = safe.strip().replace(" ", "_")
    # Limit length to 80 chars max
    return safe[:80] if len(safe) > 80 else safe

def is_valid_facebook_url(url: str) -> bool:
    """
    Very basic Facebook video URL validation.
    Supports: fb.watch, facebook.com/watch, facebook.com/reel, facebook.com/share
    """
    patterns = [
        r"(https?://)?(www\.)?facebook\.com/watch/\?v=\d+",
        r"(https?://)?fb\.watch/[A-Za-z0-9_-]+",
        r"(https?://)?(www\.)?facebook\.com/reel/[A-Za-z0-9_-]+",
        r"(https?://)?(www\.)?facebook\.com/share/[A-Za-z0-9_-]+",
    ]
    return any(re.match(p, url) for p in patterns)


def normalize_fb_url(url: str) -> str:
    """
    Normalize messy Facebook URLs into cleaner reel/watch format.
    """
    # Convert watch?v=123 → reel/123
    match = re.search(r'v=(\d+)', url)
    if match:
        return f"https://www.facebook.com/reel/{match.group(1)}/"

    # fb.watch/xyz → leave as-is (yt-dlp can handle it)
    if "fb.watch" in url:
        return url.strip()

    # Already reel/share link → return as is
    return url.strip()
