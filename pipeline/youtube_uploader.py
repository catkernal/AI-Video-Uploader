"""
YouTube Shorts Uploader via Official YouTube Data API v3
Free Quota: 10,000 units/day (1 video upload = 1,600 units -> up to 6 Shorts per day for free).
"""
import os
import json
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import re

# Scopes required for uploading YouTube videos
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

CREDENTIALS_DIR = os.path.join(os.path.dirname(__file__), "..", "credentials")
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
CLIENT_SECRETS_FILE = os.path.join(CREDENTIALS_DIR, "youtube_creds.json")
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "youtube_token.json")
MUSIC_CREDITS_FILE = os.path.join(CONFIG_DIR, "music_credits.json")

def strip_links(text):
    """
    Removes all URLs and domain links from text.
    """
    # Remove http:// or https:// URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove domain-like mentions e.g. (incompetech.com)
    text = re.sub(r'\(?\s*[\w\.-]+\.(com|org|net|io|co)\s*\)?', '', text)
    # Clean up excess whitespace while preserving line structure
    lines = [line.strip() for line in text.splitlines()]
    cleaned = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                cleaned.append("")
                prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False
    return "\n".join(cleaned).strip()

def load_music_credits():
    if os.path.exists(MUSIC_CREDITS_FILE):
        try:
            with open(MUSIC_CREDITS_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def ensure_music_credits(description, music_path=None):
    """
    Ensures the video description contains proper music credit attribution without any web links.
    """
    description = strip_links(description)
    
    if "Music Credit" not in description:
        credits_db = load_music_credits()
        attribution = None
        
        if music_path:
            rel_path = os.path.relpath(music_path, os.path.join(CONFIG_DIR, ".."))
            entry = credits_db.get(rel_path) or credits_db.get(music_path)
            if entry:
                attribution = entry.get("attribution_text")
                
        if not attribution:
            attribution = (
                "🎵 Music Credit:\n"
                '"Sneaky Snitch" Kevin MacLeod\n'
                "Licensed under Creative Commons: By Attribution 4.0 License"
            )
            
        description = f"{description}\n\n---\n{attribution}"
        
    # Strictly ensure zero links in the final description
    return strip_links(description)

def get_authenticated_service():
    """
    Authenticates with YouTube Data API v3.
    Reuses saved credentials from youtube_token.json if available.
    Otherwise initiates one-time OAuth 2.0 authorization and saves the token.
    """
    creds = None
    
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"❌ YouTube client secrets not found at: {CLIENT_SECRETS_FILE}")
        return None
        
    # Check if we already have a saved access token
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"⚠️ Error reading saved token: {e}")
            creds = None
            
    # If there are no (valid) credentials available, prompt authorization
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired YouTube token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"⚠️ Failed to refresh token: {e}, re-authenticating...")
                creds = None
                
        if not creds:
            print("\n🔐 Initiating One-Time YouTube OAuth Authorization...")
            print("A browser window will open, or follow the link to log into your YouTube account.")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            try:
                creds = flow.run_local_server(port=0, open_browser=True)
            except Exception:
                # Fallback to console code authorization if port binding or browser fails
                creds = flow.run_console()
                
            # Save the credentials for next time
            with open(TOKEN_FILE, "w") as token_out:
                token_out.write(creds.to_json())
            print(f"✅ YouTube authorization successful! Token saved to: {TOKEN_FILE}")
            
    return build("youtube", "v3", credentials=creds)

def upload_short(video_path, title, description, tags=None, privacy="public", music_path=None):
    """
    Uploads a 20-second video to YouTube Shorts.
    - Category: 24 (Entertainment)
    - Made for Kids: False ("Not made for kids")
    - Visibility: Public (default)
    - Music Credits: Appended automatically to description
    - Tags: Includes #Shorts
    """
    youtube = get_authenticated_service()
    if not youtube:
        print("❌ Could not establish YouTube connection.")
        return False
        
    # Ensure #Shorts is present in title or description
    if "#Shorts" not in title and "#Shorts" not in description:
        title = f"{title} #Shorts"
        
    tag_list = tags or ["Shorts", "KidsDance", "Animation", "AnimalDance"]
    
    # Ensure music credits attribution is included in description
    full_description = ensure_music_credits(description, music_path=music_path)
    
    body = {
        "snippet": {
            "title": title[:100],  # Max 100 chars
            "description": full_description,
            "tags": tag_list,
            "categoryId": "24"  # Entertainment
        },
        "status": {
            "privacyStatus": privacy,  # "public", "unlisted", or "private"
            "selfDeclaredMadeForKids": False  # Not made for kids
        }
    }
    
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    
    print(f"\n📤 [YouTube Shorts] Uploading: {title}")
    print(f"   • Visibility: {privacy.upper()}")
    print(f"   • Audience: Not made for kids (selfDeclaredMadeForKids=False)")
    print(f"   • Music Credit: Included in description")
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   Upload progress: {int(status.progress() * 100)}%")
            
    video_id = response.get("id")
    print(f"🎉 Successfully uploaded to YouTube Shorts!")
    print(f"🔗 Watch URL: https://youtube.com/shorts/{video_id}")
    return video_id

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload an existing video to YouTube Shorts")
    parser.add_argument("--video", type=str, default=None, help="Path to existing .mp4 video to upload")
    parser.add_argument("--title", type=str, default=None, help="Video title (defaults to cleaned filename)")
    parser.add_argument("--description", type=str, default=None, help="Video description / caption")
    parser.add_argument("--music", type=str, default=None, help="Path or name of music track used (for exact credit attribution)")
    parser.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"], help="Privacy status (default: public)")
    args = parser.parse_args()
    
    if args.video:
        if not os.path.exists(args.video):
            print(f"❌ Video file not found: {args.video}")
            exit(1)
            
        # Determine title
        if args.title:
            title = args.title
        else:
            base_name = os.path.splitext(os.path.basename(args.video))[0]
            clean_name = base_name.replace("_20s_short", "").replace("__", " & ").replace("_", " ").title()
            title = f"{clean_name} Dance Party! 🐾🎈 #Shorts"
            
        # Determine description
        if args.description:
            description = args.description
        else:
            description = (
                f"Dance along with {title}! 🌟 Join the animal dance party! Like and subscribe for more fun buddies! 🎵✨\n\n"
                "#Shorts #KidsDance #Cocomelon #AnimalDance #Animation #ViralShorts"
            )
            
        print(f"🎬 Video: {args.video}")
        print(f"📌 Title: {title}")
        print(f"🌍 Visibility: {args.privacy}")
        upload_short(args.video, title, description, privacy=args.privacy, music_path=args.music)
    else:
        print("🔍 Testing YouTube Authentication...")
        svc = get_authenticated_service()
        if svc:
            print("✅ YouTube Service Ready! You can upload videos using:")
            print("   python pipeline/youtube_uploader.py --video output/<video_file>.mp4 --privacy public")
