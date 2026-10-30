# 🎬 AI Kids Dance Shorts — Autonomous Production Pipeline

An end-to-end automated pipeline that generates and publishes **20-second viral 3D CGI kids dance videos** to **YouTube Shorts** using 100% free-tier AI tools, royalty-free children's music, and official APIs.

---

## 🌟 Key Features

* **40 Permanent Characters:** 39 animals + Timmy the Boy, each with permanent names, signature outfits, and accessories (e.g. *Buddy the Dog, Whiskers the Cat, Jumbo the Elephant*).
* **Dynamic Cast Sizes:** Randomly selects **Solo (1)**, **Duo (2)**, or **Trio (3)** performers per video.
* **Standardized 3D CGI Prompt Engine:** Generates Pixar / Cocomelon style prompts with dynamic scenes, weather, camera angles, and dance moves.
* **33 High-Beat 20s Music Tracks:** Curated and cut to exact 20.0-second high-energy windows from the YouTube Audio Library and Creative Commons (Incompetech).
* **Automatic Legal Attribution:** Automatically injects the correct music credits and CC-BY 4.0 licenses into every short description upon upload.
* **Free-Tier Video Diffusion:** Interfaces with free Hugging Face ZeroGPU Spaces (*Wan 2.1, CogVideoX, LTX-Video*) via `gradio_client`.
* **Official YouTube Data API v3 Upload:** Seamlessly uploads directly to YouTube Shorts with #Shorts tags, Made for Kids status, and configurable privacy.
* **Autonomous 24h Scheduler:** Runs in the background and publishes daily on autopilot.

---

## 📁 Project Structure

```
AI-Videos/
├── .env                       # HF_TOKEN (Hugging Face Access Token)
├── .gitignore                 # Protects secrets, tokens, and heavy videos
├── main.py                    # Master CLI orchestrator
├── schedule_runner.py         # Autonomous 24-hour background scheduler
│
├── config/
│   ├── animals.json           # 40 permanent character profiles
│   ├── scenes_and_moves.json  # Scenes, weather, camera shots, and choreography
│   ├── templates.json         # Prompt templates and dynamic grammar
│   └── music_credits.json     # Copyright and attribution registry for all tracks
│
├── assets/
│   └── music/                 # 33 polished 20-second high-beat MP3/WAV tracks
│
├── credentials/
│   ├── youtube_creds.json     # Google Cloud OAuth 2.0 Client Secret (Desktop App)
│   └── youtube_token.json     # (Generated) Cached refresh token for headless uploads
│
├── pipeline/
│   ├── generator.py           # Random cast, prompt & metadata generator
│   ├── composer.py            # Local FFmpeg 20s looper, audio mixer & title overlay
│   ├── video_generator.py     # Hugging Face ZeroGPU client
│   └── youtube_uploader.py    # Official YouTube Data API v3 uploader
│
└── output/                    # Staging folder for final rendered 20s MP4 shorts
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
* Python 3.10+
* FFmpeg installed on system

### 2. Environment Setup
The project uses a local virtual environment:
```bash
# Activate virtual environment
source .venv/bin/activate
```

### 3. Configure Hugging Face Token
Add your free Hugging Face token in `.env`:
```ini
HF_TOKEN=hf_your_free_huggingface_token
```

### 4. Configure YouTube API (One-Time Setup)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable **YouTube Data API v3** (Free quota: 10,000 units/day = up to 6 Shorts daily).
3. Create an **OAuth 2.0 Client ID** (Application type: *Desktop App*).
4. Download the JSON file and save it as:
   ```
   credentials/youtube_creds.json
   ```
5. Run the one-time authentication:
   ```bash
   .venv/bin/python pipeline/youtube_uploader.py
   ```
   *Your browser will open to grant access. Once approved, `credentials/youtube_token.json` is saved permanently, allowing 100% headless uploads.*

---

## 🎮 Usage Guide

### Generate a Video Locally (No Upload)
```bash
# Random cast (1 to 3 characters):
.venv/bin/python main.py

# Force specific group size:
.venv/bin/python main.py --count 1    # Solo dance
.venv/bin/python main.py --count 2    # Duo dance
.venv/bin/python main.py --count 3    # Trio dance
```

### Generate & Upload Directly to YouTube Shorts
```bash
# Upload as Public:
.venv/bin/python main.py --upload

# Upload as Unlisted (recommended for initial testing):
.venv/bin/python main.py --upload --privacy unlisted
```

### Use Custom Video Footage / Existing Clip
```bash
.venv/bin/python main.py --clip path/to/my_dance.mp4 --upload
```

### Run Autonomous Daily Scheduler (Everyday at 8:01 AM)
```bash
# Run in the background (publishes everyday at 08:01 AM):
.venv/bin/python schedule_runner.py &
```

Or set up a standard Linux `cron` job:
```bash
crontab -e
```
Add:
```cron
1 8 * * * cd /home/karthikeya/Desktop/Projects/AI-Videos && /home/karthikeya/Desktop/Projects/AI-Videos/.venv/bin/python main.py --upload >> output/cron.log 2>&1
```

---

## 📜 Music & Copyright Credits

All music tracks in `assets/music/` are:
* Selected from YouTube Audio Library / Creative Commons: By Attribution 4.0.
* Primary composer: **Kevin MacLeod** ([incompetech.com](https://incompetech.com)).
* Every short automatically includes the mandatory license attribution in its description upon upload, ensuring 100% copyright safety and monetization compliance.

---

## 📄 License
This project is for personal and creator automation use.

