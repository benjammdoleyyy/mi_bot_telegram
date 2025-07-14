import os
import re
import logging
from instaloader import Instaloader, Post

logger = logging.getLogger(__name__)

loader = Instaloader()
SESSION_FILE = f"{os.getcwd()}/session-instaloader"

def is_valid_instagram_url(url: str) -> bool:
    return bool(re.match(r"https?://(www\.)?instagram\.com/(p|reel|tv)/", url))

def extract_shortcode(instagram_post: str) -> str:
    match = re.search(r"instagram\.com/(?:p|reel|tv)/([^/?#&]+)", instagram_post)
    return match.group(1) if match else None

def fetch_instagram_data(instagram_post: str) -> str:
    shortcode = extract_shortcode(instagram_post)
    if not shortcode:
        return None

    try:
        post = Post.from_shortcode(loader.context, shortcode)
        if post.is_video:
            return post.video_url
        else:
            return post.url
    except Exception as e:
        logger.error(f"Error fetching Instagram data: {e}")
        return None
