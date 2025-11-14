import time
import os
import logging
from app.config import SHOTSTACK_API_KEY, SHOTSTACK_STAGE, RENDER_BACKEND
from shotstack_sdk.api import edit_api
from shotstack_sdk.model.clip import Clip
from shotstack_sdk.model.track import Track
from shotstack_sdk.model.timeline import Timeline
from shotstack_sdk.model.output import Output
from shotstack_sdk.model.edit import Edit
from shotstack_sdk.model.video_asset import VideoAsset
from shotstack_sdk.model.audio_asset import AudioAsset
from shotstack_sdk.model.soundtrack import Soundtrack
from shotstack_sdk.model.title_asset import TitleAsset
import shotstack_sdk

DEV_FALLBACK_MODE = (
    os.getenv("AUTOVIDAI_DEV_MODE", "").lower() in {"1", "true", "yes"}
    or (not SHOTSTACK_API_KEY) or (isinstance(SHOTSTACK_API_KEY, str) and SHOTSTACK_API_KEY.startswith("dev_"))
)

def _local_ffmpeg_available() -> bool:
    from shutil import which
    return which("ffmpeg") is not None

def _download_if_remote(url: str, dest_dir: str) -> str:
    if not _is_url(url):
        return url
    import requests, hashlib
    os.makedirs(dest_dir, exist_ok=True)
    fname = hashlib.md5(url.encode()).hexdigest() + ".mp4"
    dest = os.path.join(dest_dir, fname)
    if os.path.exists(dest):
        return dest
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(dest, "wb") as f: f.write(r.content)
        return dest
    except Exception as e:
        logging.warning("Failed to download %s: %s", url, e)
        return url  # fall back to original

def _merge_video_audio(video_path: str, audio_path: str, out_path: str, narration: str | None = None):
    # Basic ffmpeg merge; ignore narration text overlay for now to keep dependency surface minimal.
    # If narration provided, could add subtitles or drawtext (requires font & escaping).
    import subprocess
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-filter:a", "aresample=async=1",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
        "-c:a", "aac", "-shortest",
        out_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logging.warning("ffmpeg merge failed for %s + %s: %s", video_path, audio_path, e)
        return False

def _concat_videos(video_paths: list, out_path: str):
    import subprocess, tempfile
    list_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
    for p in video_paths:
        list_file.write(f"file '{p}'\n")
    list_file.flush()
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file.name, "-c:v", "libx264", "-c:a", "aac", out_path]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logging.warning("ffmpeg concat failed: %s", e)
        return False
    finally:
        try:
            list_file.close()
            os.unlink(list_file.name)
        except Exception:
            pass

def _reencode_uniform(video_paths: list, temp_dir: str) -> list:
    """Re-encode each video to a uniform codec/container to improve concat reliability.

    Returns list of re-encoded paths (or original if re-encode fails)."""
    import subprocess
    uniform_paths = []
    for i, src in enumerate(video_paths):
        out = os.path.join(temp_dir, f"uniform_{i}.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", src,
            "-filter:a", "aresample=async=1",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
            "-c:a", "aac", "-ar", "44100", "-b:a", "128k",
            out
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            uniform_paths.append(out)
        except Exception as e:
            logging.warning("Uniform re-encode failed for %s: %s (will use original)", src, e)
            uniform_paths.append(src)
    return uniform_paths

def _local_render(scenes: list, title: str) -> dict:
    if not _local_ffmpeg_available():
        return {"error": "ffmpeg not available for local renderer"}
    if not scenes:
        return {"error": "No scenes provided for local render"}
    logging.info("Local renderer active: assembling %d scenes", len(scenes))
    temp_dir = os.path.join("temp", "render_local")
    os.makedirs(temp_dir, exist_ok=True)
    fast_mode = os.getenv("FAST_MODE", "").lower() in {"1", "true", "yes"}
    scene_iter = scenes[:3] if fast_mode else scenes

    def build_segment(idx: int, scene: dict) -> str | None:
        import subprocess, shutil
        video_src = _download_if_remote(scene["video_url"], temp_dir)
        # Determine intended duration heuristic
        words_per_second = 2.5
        base_duration = max(len(scene.get("narration", "").split()) / words_per_second, 3.0)
        duration = min(base_duration, 4.0) if fast_mode else base_duration
        segment_path = os.path.join(temp_dir, f"segment_{idx}.mp4")
        audio_src = scene.get("audio_path") if scene.get("audio_path") else None
        # Treat tiny placeholder audio (< 2KB) as invalid and replace with silence
        if audio_src and (not os.path.exists(audio_src) or os.path.getsize(audio_src) < 2048):
            audio_src = None
        # Build ffmpeg command: always re-encode for uniformity
        if audio_src:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_src,
                "-i", audio_src,
                "-filter:a", "aresample=async=1",
                "-t", f"{duration:.2f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
                "-c:a", "aac",
                segment_path
            ]
        else:
            # Generate silent audio via anullsrc
            cmd = [
                "ffmpeg", "-y",
                "-i", video_src,
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-shortest",
                "-filter:a", "aresample=async=1",
                "-t", f"{duration:.2f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
                "-c:a", "aac",
                segment_path
            ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return segment_path
        except Exception as e:
            logging.warning("Segment build failed (video+audio) idx=%d: %s", idx, e)
            # Fallback: video only re-encode
            fallback_path = os.path.join(temp_dir, f"segment_{idx}_videoonly.mp4")
            cmd2 = [
                "ffmpeg", "-y", "-i", video_src,
                "-t", f"{duration:.2f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
                fallback_path
            ]
            try:
                subprocess.run(cmd2, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return fallback_path
            except Exception as e2:
                logging.error("Video-only fallback failed idx=%d: %s", idx, e2)
                return None

    segment_paths = []
    for idx, scene in enumerate(scene_iter):
        path = build_segment(idx, scene)
        if path:
            segment_paths.append(path)
        else:
            logging.warning("Skipping scene %d due to segment build failure", idx)

    if not segment_paths:
        return {"error": "All segments failed to build"}

    final_out = os.path.join(temp_dir, "final_video.mp4")
    if len(segment_paths) == 1:
        import shutil
        try:
            shutil.copyfile(segment_paths[0], final_out)
        except Exception as e:
            logging.error("Single segment copy failed: %s", e)
            return {"error": "Local rendering failed (copy)"}
        logging.info("Local render complete (single segment): %s", final_out)
        return {"final_video_url": final_out, "local": True}

    # Concatenate uniformly encoded segments
    ok = _concat_videos(segment_paths, final_out)
    if not ok:
        logging.warning("Concat failed even after uniform encode; attempting second pass with re-encode")
        uniform_paths = _reencode_uniform(segment_paths, temp_dir)
        ok2 = _concat_videos(uniform_paths, final_out)
        if not ok2:
            return {"error": "Local concatenation failed after re-encode"}
    logging.info("Local render complete: %s", final_out)
    return {"final_video_url": final_out, "local": True}

def _is_url(path: str) -> bool:
    return isinstance(path, str) and (path.startswith("http://") or path.startswith("https://"))

def render_video(scenes: list, title: str) -> dict:
    fast_mode = os.getenv("FAST_MODE", "").lower() in {"1", "true", "yes"}
    print("--- Stage 4: Renderer (Using Shotstack) ---")
    logging.info("Shotstack environment: %s | fast_mode=%s", SHOTSTACK_STAGE, fast_mode)
    if RENDER_BACKEND == "local":
        return _local_render(scenes, title)
    if DEV_FALLBACK_MODE:
        logging.warning("Dev fallback active for Stage 4 — using local renderer stub.")
        return _local_render(scenes, title)
    configuration = shotstack_sdk.Configuration(host="https://api.shotstack.io/" + SHOTSTACK_STAGE)
    with shotstack_sdk.ApiClient(configuration) as api_client:
        api_client.set_default_header('x-api-key', SHOTSTACK_API_KEY)
        api_instance = edit_api.EditApi(api_client)
        video_clips, audio_clips, caption_clips = [], [], []
        start_time = 0.0
        # Optionally limit scenes and reduce duration in fast mode (sandbox credit-friendly)
        scene_iter = scenes[:3] if fast_mode else scenes
        for scene in scene_iter:
            words_per_second = 2.5
            base_duration = max(len(scene["narration"].split()) / words_per_second, 3.0)
            duration = min(base_duration, 4.0) if fast_mode else base_duration
            video_clips.append(Clip(asset=VideoAsset(src=scene["video_url"], volume=0.0), start=start_time, length=duration))
            audio_src = scene.get("audio_path")
            if _is_url(audio_src):
                audio_clips.append(Clip(asset=AudioAsset(src=audio_src, volume=1.0), start=start_time, length=duration))
            else:
                logging.warning("Skipping non-URL audio asset for scene at start %.2f: %s", start_time, audio_src)
            caption_asset = TitleAsset(text=scene["narration"], style="subtitle")
            caption_clips.append(Clip(asset=caption_asset, start=start_time, length=duration))
            start_time += duration
        soundtrack = None if fast_mode else Soundtrack(src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", effect="fadeInFadeOut", volume=0.1)
        # If we have no per-scene audio clips, provide a soft global soundtrack even in fast mode
        if not audio_clips:
            soundtrack = Soundtrack(src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", effect="fadeInFadeOut", volume=0.1)
        tracks = [Track(clips=video_clips)]
        if audio_clips:
            tracks.append(Track(clips=audio_clips))
        tracks.append(Track(clips=caption_clips))
        timeline = Timeline(background="#000000", tracks=tracks, soundtrack=soundtrack)
        output = Output(format="mp4", resolution="1080")
        edit = Edit(timeline=timeline, output=output)
        try:
            print("Sending render request to Shotstack...")
            api_response = api_instance.post_render(edit)
            render_id = api_response['response']['id']
            print(f"Request accepted. Render ID: {render_id}")
            print("Waiting for render to complete... (this may take a few minutes)")
            poll_interval = 6 if fast_mode else 10
            while True:
                time.sleep(poll_interval)
                status_response = api_instance.get_render(render_id)
                status = status_response['response']['status']
                print(f"  -> Current status: {status}")
                if status == 'done':
                    final_video_url = status_response['response']['url']
                    print("✅ Video rendered successfully!")
                    return {"final_video_url": final_video_url}
                elif status in ['failed', 'cancelled']:
                    error_message = status_response['response'].get('error', 'Unknown render failure.')
                    print(f"❌ Video rendering failed: {error_message}")
                    return {"error": "Shotstack rendering failed"}
        except Exception as e:
            print(f"❌ Error calling Shotstack API: {e}")
            return {"error": f"Shotstack API request failed: {e}"}
