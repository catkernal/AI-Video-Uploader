"""
Hugging Face Video Generation Client
Leverages free ZeroGPU Spaces (Lightricks/ltx-video-distilled) via gradio_client.

Key design choices:
  - Native 9:16 generation (432×768) — no cropping needed downstream.
  - Reference-image consistency: the first clip is generated text-to-video,
    its first frame is extracted, and all subsequent clips use image-to-video
    with that frame so the character design stays locked in.
"""
import os
import shutil
import subprocess
from dotenv import load_dotenv

# Explicitly resolve .env path relative to this project root so it loads regardless of CWD
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=ENV_PATH)
HF_TOKEN = os.getenv("HF_TOKEN")

FFMPEG_BIN = "/home/karthikeya/.cache/Cypress/13.13.0/Cypress/resources/app/node_modules/@ffmpeg-installer/linux-x64/ffmpeg"

# Native 9:16 — width:height = 432:768  (9/16 = 0.5625 exact)
VIDEO_WIDTH = 432
VIDEO_HEIGHT = 768

LTX_SPACE = "Lightricks/ltx-video-distilled"
NEGATIVE_PROMPT = (
    "worst quality, inconsistent motion, blurry, jittery, distorted, "
    "extra limbs, deformed, static, frozen, ugly, text, watermark"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_client_cache = None

def _get_client():
    """Lazy-load and cache the gradio client so we don't reconnect every call."""
    global _client_cache
    if _client_cache is None:
        from gradio_client import Client
        _client_cache = Client(LTX_SPACE, token=HF_TOKEN)
    return _client_cache


def _extract_video_path(result):
    """Pull the local video file path out of various gradio return shapes."""
    if isinstance(result, (tuple, list)):
        item = result[0]
        if isinstance(item, dict):
            return item.get("video")
        return str(item)
    if isinstance(result, dict):
        return result.get("video")
    if isinstance(result, str):
        return result
    return None


def extract_first_frame(video_path, output_image_path=None):
    """Extract the first frame of a video as a PNG using FFmpeg."""
    if output_image_path is None:
        output_image_path = video_path.rsplit(".", 1)[0] + "_ref.png"
    subprocess.run(
        [FFMPEG_BIN, "-i", video_path, "-frames:v", "1",
         "-update", "1", output_image_path, "-y"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )
    if os.path.exists(output_image_path):
        return output_image_path
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_video_clip(prompt, output_clip_path="assets/generated_clip.mp4",
                        reference_image=None):
    """
    Generate a single ~4 s video clip at native 9:16.

    If *reference_image* is provided, image-to-video mode is used so that the
    character design matches the reference.  Otherwise text-to-video is used.
    """
    os.makedirs(os.path.dirname(output_clip_path), exist_ok=True)

    if not HF_TOKEN:
        print("⚠️  HF_TOKEN not found in .env!")
        return None

    print(f"   📝 Prompt: {prompt[:120]}...")

    try:
        client = _get_client()

        if reference_image and os.path.exists(reference_image):
            # ---------- image-to-video (consistent characters) ----------
            from gradio_client import handle_file
            result = client.predict(
                prompt=prompt,
                negative_prompt=NEGATIVE_PROMPT,
                input_image_filepath=handle_file(reference_image),
                input_video_filepath=None,
                height_ui=VIDEO_HEIGHT,
                width_ui=VIDEO_WIDTH,
                mode="image-to-video",
                duration_ui=4,
                ui_frames_to_use=9,
                seed_ui=42,
                randomize_seed=True,
                ui_guidance_scale=3.0,
                improve_texture_flag=True,
                api_name="/image_to_video",
            )
        else:
            # ---------- text-to-video (first clip, or fallback) ----------
            result = client.predict(
                prompt=prompt,
                negative_prompt=NEGATIVE_PROMPT,
                input_image_filepath=None,
                input_video_filepath=None,
                height_ui=VIDEO_HEIGHT,
                width_ui=VIDEO_WIDTH,
                mode="text-to-video",
                duration_ui=4,
                ui_frames_to_use=9,
                seed_ui=42,
                randomize_seed=True,
                ui_guidance_scale=3.0,
                improve_texture_flag=True,
                api_name="/text_to_video",
            )

        video_file = _extract_video_path(result)
        if video_file and os.path.exists(video_file):
            shutil.copy(video_file, output_clip_path)
            print(f"   ✅ Clip saved: {output_clip_path}")
            return output_clip_path
        else:
            print(f"   ⚠️  Unexpected result: {result}")
    except Exception as e:
        print(f"   ⚠️  Generation error: {e}")

    return None


def generate_multi_shot_clips(shots_plan, safe_name, reference_image=None):
    """
    Generate all clips for a multi-shot choreography plan.

    Shot 1 → text-to-video   (establishes the character look)
    Shots 2–N → image-to-video using shot 1's first frame as reference

    Returns a list of output clip paths (only successfully generated ones).
    """
    os.makedirs("assets", exist_ok=True)
    clips = []
    ref_image = reference_image  # may be None initially

    for shot in shots_plan:
        idx = shot["index"]
        total = len(shots_plan)
        clip_path = os.path.join("assets", f"{safe_name}_shot_{idx}.mp4")
        print(f"\n   ▶ Shot {idx}/{total}  •  {shot['body_part']}  •  {shot['shot']}")

        generated = generate_video_clip(
            prompt=shot["prompt"],
            output_clip_path=clip_path,
            reference_image=ref_image,
        )

        if generated and os.path.exists(generated):
            clips.append(generated)
            # After the first successful clip, extract reference frame
            if ref_image is None:
                ref_path = os.path.join("assets", f"{safe_name}_ref.png")
                ref_image = extract_first_frame(generated, ref_path)
                if ref_image:
                    print(f"   🖼️  Reference frame extracted: {ref_image}")
        else:
            print(f"   ❌ Shot {idx}/{total} generation failed!")
            # Stop early to avoid wasted API calls and ensure incomplete sequences are not uploaded
            break

    return clips


if __name__ == "__main__":
    test_prompt = (
        "A cute 3D Pixar puppy dancing happily with jazz hands in a living room, "
        "vertical 9:16 video, cheerful lighting"
    )
    generate_video_clip(test_prompt)
