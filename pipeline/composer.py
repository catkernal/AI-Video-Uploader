import os
import subprocess

FFMPEG_BIN = "/home/karthikeya/.cache/Cypress/13.13.0/Cypress/resources/app/node_modules/@ffmpeg-installer/linux-x64/ffmpeg"

def compose_20s_short(input_videos, music_path, output_path,
                      title_display="Animal Dance Party!"):
    """
    Stitch multiple AI-generated clips into a single 20-second 9:16 Short.

    - Multi-clip (≥2): concatenates each trimmed to an equal share of 20 s.
    - Single clip: loops to fill 20 s.

    Audio from *music_path* is mixed in at boosted volume with a smooth fade-out.
    The video is scaled to 720×1280 (true 9:16) — no cropping since the source
    clips are already generated at native 9:16 (432×768).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    target_duration = 20.0

    if isinstance(input_videos, str):
        clip_list = [input_videos]
    else:
        clip_list = list(input_videos)

    n = len(clip_list)
    print(f"🎬 Composing 20-second short: {title_display}  ({n} clip(s))...")

    # Sanitize title for FFmpeg drawtext (escape single quotes, colons)
    safe_title = title_display.replace("'", "'\\''").replace(":", "\\:")

    if n > 1:
        # ── Multi-clip assembly ───────────────────────────────────────
        seg_dur = target_duration / n
        inputs = []
        filter_parts = []
        concat_in = ""

        for i, clip in enumerate(clip_list):
            inputs += ["-i", clip]
            # Scale to exactly 720×1280 (true 9:16), trim to segment length
            filter_parts.append(
                f"[{i}:v]scale=720:1280,trim=0:{seg_dur},setpts=PTS-STARTPTS[v{i}];"
            )
            concat_in += f"[v{i}]"

        music_idx = n
        inputs += ["-i", music_path]

        filter_parts.append(
            f"{concat_in}concat=n={n}:v=1:a=0,"
            f"drawtext=text='{safe_title}':"
            f"fontcolor=white:fontsize=42:box=1:boxcolor=black@0.4:"
            f"boxborderw=10:x=(w-text_w)/2:y=120[v];"
            f"[{music_idx}:a]volume=1.5,atrim=0:{target_duration},"
            f"afade=t=out:st=18.5:d=1.5[a]"
        )

        cmd = [
            FFMPEG_BIN,
            *inputs,
            "-filter_complex", "".join(filter_parts),
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-disposition:a:0", "default",
            "-movflags", "+faststart",
            output_path, "-y",
        ]
    else:
        # ── Single clip: loop to fill 20 s ────────────────────────────
        cmd = [
            FFMPEG_BIN,
            "-stream_loop", "5",
            "-i", clip_list[0],
            "-i", music_path,
            "-t", str(target_duration),
            "-filter_complex",
            (
                f"[0:v]scale=720:1280,"
                f"drawtext=text='{safe_title}':"
                f"fontcolor=white:fontsize=42:box=1:boxcolor=black@0.4:"
                f"boxborderw=10:x=(w-text_w)/2:y=120[v];"
                f"[1:a]volume=1.5,atrim=0:{target_duration},"
                f"afade=t=out:st=18.5:d=1.5[a]"
            ),
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-disposition:a:0", "default",
            "-movflags", "+faststart",
            output_path, "-y",
        ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        stderr_text = result.stderr.decode(errors="replace")
        print(f"⚠️  FFmpeg primary pass failed, retrying without drawtext...")
        # Fallback — drop drawtext in case of font issues
        cmd_fb = [
            FFMPEG_BIN,
            "-stream_loop", "5",
            "-i", clip_list[0],
            "-i", music_path,
            "-t", str(target_duration),
            "-filter_complex",
            (
                f"[0:v]scale=720:1280[v];"
                f"[1:a]volume=1.5,atrim=0:{target_duration},"
                f"afade=t=out:st=18.5:d=1.5[a]"
            ),
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart",
            output_path, "-y",
        ]
        subprocess.run(cmd_fb, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f"✅ 20-second short rendered → {output_path}")
    return output_path
