"""
Master End-to-End Orchestrator for Automated 20s AI Kids Dance Shorts

Default mode (Solution B):
  1. Selects 1–3 random characters from 40-animal pool.
  2. Builds a 6-shot choreography plan — each shot uses a different body-part
     movement (hands, legs, hips, head, full-body) for variety.
  3. Generates clip 1 via text-to-video, extracts a reference frame,
     then generates clips 2–6 via image-to-video for character consistency.
  4. Stitches the 6 clips into a 20-second 9:16 Short with music & title.
"""
import os
import re
import glob
import argparse
from pipeline.generator import build_next_short_spec
from pipeline.composer import compose_20s_short
from pipeline.video_generator import generate_multi_shot_clips, generate_video_clip
from pipeline.youtube_uploader import upload_short

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def run_pipeline(num_animals=None, input_clip=None,
                 auto_upload=False, privacy="public"):
    print("=" * 60)
    print("🎬  STARTING 20-SECOND AI SHORT GENERATION PIPELINE")
    print("=" * 60)

    # 1. Build specification ─────────────────────────────────────────
    spec = build_next_short_spec(num_animals=num_animals)
    chars = spec["characters"]

    print(f"\n🐾 Cast ({spec['num_characters']}): {spec['characters_names']}")
    for c in chars:
        print(f"   • {c['name']} the {c['type']}  ({c['color']}, {c['accessory']})")
    print(f"📍 Scene: {spec['scene']}")
    print(f"🎵 Music: {os.path.basename(spec['music_path'] or 'default')}")

    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', spec['characters_names'].lower())

    # 2. Generate clips ──────────────────────────────────────────────
    if input_clip:
        if not os.path.exists(input_clip):
            print(f"❌ Input clip not found: {input_clip}")
            return False
        clips = [input_clip]
    else:
        plan = spec.get("shots_plan", [])
        total_shots = len(plan)
        print(f"\n🎥  {total_shots}-Shot Choreography Plan:")
        for s in plan:
            print(f"    Shot {s['index']}  [{s['body_part']}]  "
                  f"{s['dance_move'][:65]}…")

        print(f"\n🤖  Generating {total_shots} clips via Hugging Face "
              f"(native 9:16, 432×768)…")
        clips = generate_multi_shot_clips(plan, safe_name)

        # STRICT CHECK: If any shot generation failed, DO NOT PROCEED WITH UPLOAD
        if len(clips) < total_shots:
            print(f"\n❌ Shot generation incomplete: Generated {len(clips)} of {total_shots} planned shots.")
            print("⛔ Aborting pipeline: Will NOT compose or upload video when shot generation fails.")
            return False

    # 3. Compose 20-second Short ─────────────────────────────────────
    output_path = os.path.join(OUTPUT_DIR,
                               f"{safe_name}_20s_short.mp4")
    music_track = spec["music_path"] or "assets/music/track_01_kids_dance.wav"

    composed = compose_20s_short(
        input_videos=clips,
        music_path=music_track,
        output_path=output_path,
        title_display=f"{spec['characters_names']} Dance!",
    )

    print(f"\n✨  Final Short: {composed}")
    print(f"🔊  Audio: {os.path.basename(music_track)} (1.5× boost, AAC 192 kbps)")
    print(f"📌  Title: {spec['title']}")
    print(f"📌  Caption:\n{spec['caption']}")

    # 4. Upload ──────────────────────────────────────────────────────
    if auto_upload:
        print("\n🚀  Uploading to YouTube Shorts…")
        upload_short(composed, spec["title"], spec["caption"], privacy=privacy, music_path=music_track)
    else:
        print("\n💡  Saved to output/.  Upload with:  python3 main.py --upload")

    return composed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a 20-second AI Kids Dance YouTube Short"
    )
    parser.add_argument("--count", type=int, default=None,
                        help="Number of animal characters (1–3)")
    parser.add_argument("--clip", type=str, default=None,
                        help="Path to a pre-existing raw video clip")
    parser.add_argument("--upload", action="store_true",
                        help="Auto-upload the finished Short to YouTube")
    parser.add_argument("--privacy", type=str, default="public",
                        choices=["public", "unlisted", "private"],
                        help="YouTube privacy status")
    args = parser.parse_args()

    run_pipeline(
        num_animals=args.count,
        input_clip=args.clip,
        auto_upload=args.upload,
        privacy=args.privacy,
    )
