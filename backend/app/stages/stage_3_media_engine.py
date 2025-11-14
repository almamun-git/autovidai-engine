import os
import requests
import logging
import subprocess
from app.config import (
    PEXELS_API_KEY,
    ELEVENLABS_API_KEY,
    MEDIA_SOURCE,
    STABLE_VIDEO_SERVER_URL,
    STABLE_VIDEO_POLL_INTERVAL,
    STABLE_VIDEO_MAX_POLL,
    TTS_SOURCE,
)

DEV_FALLBACK_MODE = (
    os.getenv("AUTOVIDAI_DEV_MODE", "").lower() in {"1", "true", "yes"}
    or not PEXELS_API_KEY or (isinstance(PEXELS_API_KEY, str) and PEXELS_API_KEY.startswith("dev_"))
    or not ELEVENLABS_API_KEY or (isinstance(ELEVENLABS_API_KEY, str) and ELEVENLABS_API_KEY.startswith("dev_"))
)

# Allow placeholders in Stage 3 even in prod to avoid total pipeline failure if a single provider fails
ALLOW_PLACEHOLDER = os.getenv("STAGE3_ALLOW_PLACEHOLDER", "1").lower() in {"1", "true", "yes"}

def _simplify_query(q: str) -> str:
    q = q or ""
    # Remove known prefixes and keep first 5 words for better Pexels matching
    q = q.replace("B-roll illustrating:", "").replace("Dynamic macro shot related to", "").strip()
    words = q.split()
    return " ".join(words[:5]) or "nature"

def get_video_from_pexels(query: str, scene_index: int) -> dict:
    print(f"  - Searching Pexels for video: '{query}'")
    if DEV_FALLBACK_MODE:
        # Return a public sample video URL suitable for testing.
        url = "https://www.w3schools.com/html/mov_bbb.mp4"
        print(f"    -> ⚙️ Dev fallback video: {url}")
        return {"video_url": url, "fallback": True}
    headers = {'Authorization': PEXELS_API_KEY}
    # Try simplified query first with a few candidates
    simple = _simplify_query(query)
    params = {'query': simple,'per_page': 5}
    try:
        response = requests.get('https://api.pexels.com/videos/search', headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('videos'):
            # Prefer vertical HD then any HD then first available
            for video in data['videos']:
                video_files = video.get('video_files', [])
                # vertical hd
                for vf in video_files:
                    if vf.get('quality') == 'hd' and vf.get('width',0) < vf.get('height',0):
                        url = vf.get('link'); print(f"    -> ✅ Found vertical HD: {url}"); return {"video_url": url}
                # any hd
                for vf in video_files:
                    if vf.get('quality') == 'hd':
                        url = vf.get('link'); print(f"    -> ✅ Found HD: {url}"); return {"video_url": url}
                # any
                if video_files:
                    url = video_files[0].get('link'); print(f"    -> ✅ Found video: {url}"); return {"video_url": url}
        print(f"    -> ⚠️ No suitable video found on Pexels for query: '{query}'")
        if ALLOW_PLACEHOLDER:
            url = "https://www.w3schools.com/html/mov_bbb.mp4"
            print(f"    -> 🔁 Using placeholder video: {url}")
            return {"video_url": url, "placeholder": True}
        return {"error": "No video found on Pexels"}
    except requests.RequestException as e:
        print(f"    -> ❌ Pexels API Error: {e}")
        if ALLOW_PLACEHOLDER:
            url = "https://www.w3schools.com/html/mov_bbb.mp4"
            print(f"    -> 🔁 Using placeholder video due to error: {url}")
            return {"video_url": url, "placeholder": True}
        return {"error": "Pexels API request failed", "details": str(e)}

def _generate_silent_audio(scene_index: int, duration: float = 1.0) -> str:
    """Generate a proper silent AAC/mp3 audio file instead of a placeholder stub.

    Uses ffmpeg anullsrc if available; falls back to tiny placeholder bytes otherwise.
    """
    os.makedirs("temp", exist_ok=True)
    audio_filename = f"temp/audio_scene_{scene_index}.mp3"
    try:
        # Prefer ffmpeg if installed
        if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0:
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", f"{duration:.2f}",
                "-q:a", "5",
                audio_filename
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Fallback tiny valid-ish MP3 header (still silence-ish)
            with open(audio_filename, 'wb') as f:
                f.write(b"ID3\x04\x00\x00\x00\x00\x00\x0Fsilence")
    except Exception as e:
        logging.warning("Silent audio generation failed: %s", e)
        # Last resort placeholder
        with open(audio_filename, 'wb') as f:
            f.write(b"ID3\x04\x00\x00\x00\x00\x00\x0Ffallback")
    return audio_filename

def _tts_local_engine(text: str, scene_index: int) -> dict:
    """Generate narration using local TTS engine (pyttsx3).

    Produces a WAV then converts to MP3 if ffmpeg available; else leaves WAV.
    Returns audio_path pointing to resulting file.
    """
    try:
        import pyttsx3  # lightweight, offline
    except Exception as e:
        logging.warning("pyttsx3 not available: %s (falling back to silence)", e)
        return {"audio_path": _generate_silent_audio(scene_index), "fallback": True}
    os.makedirs("temp", exist_ok=True)
    wav_path = f"temp/audio_scene_{scene_index}.wav"
    engine = pyttsx3.init()
    # Slightly faster speech for short-form pacing
    rate = engine.getProperty('rate')
    try:
        engine.setProperty('rate', int(rate * 1.05))
    except Exception:
        pass
    try:
        engine.save_to_file(text, wav_path)
        engine.runAndWait()
    except Exception as e:
        logging.warning("Local TTS generation failed: %s", e)
        return {"audio_path": _generate_silent_audio(scene_index), "fallback": True}
    # Convert to mp3 if ffmpeg exists
    mp3_path = f"temp/audio_scene_{scene_index}.mp3"
    if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0:
        try:
            subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "4", mp3_path],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"audio_path": mp3_path, "local_tts": True}
        except Exception as e:
            logging.warning("ffmpeg mp3 conversion failed: %s", e)
            return {"audio_path": wav_path, "local_tts": True, "format": "wav"}
    return {"audio_path": wav_path, "local_tts": True, "format": "wav"}

def _tts_elevenlabs(text: str, scene_index: int) -> dict:
    if DEV_FALLBACK_MODE or not ELEVENLABS_API_KEY:
        audio_filename = _generate_silent_audio(scene_index)
        print(f"    -> ⚙️ Dev/placeholder silent audio: {audio_filename}")
        return {"audio_path": audio_filename, "fallback": True}
    voice_id = "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {'Accept': 'audio/mpeg','Content-Type': 'application/json','xi-api-key': ELEVENLABS_API_KEY}
    payload = {'text': text,'model_id': 'eleven_monolingual_v1','voice_settings': {'stability': 0.5,'similarity_boost': 0.75}}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        os.makedirs('temp', exist_ok=True)
        audio_filename = f"temp/audio_scene_{scene_index}.mp3"
        with open(audio_filename, 'wb') as f: f.write(response.content)
        print(f"    -> ✅ TTS audio saved: {audio_filename}")
        return {"audio_path": audio_filename}
    except requests.RequestException as e:
        print(f"    -> ❌ ElevenLabs API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"      -> Response: {e.response.text}")
        if ALLOW_PLACEHOLDER:
            audio_filename = _generate_silent_audio(scene_index)
            print(f"    -> 🔁 Using silent placeholder audio: {audio_filename}")
            return {"audio_path": audio_filename, "placeholder": True}
        return {"error": "ElevenLabs API request failed", "details": str(e)}

def get_audio(text: str, scene_index: int) -> dict:
    print(f"  - Generating TTS audio (source={TTS_SOURCE}) for: '{text[:50]}...'")
    if TTS_SOURCE == 'local':
        return _tts_local_engine(text, scene_index)
    return _tts_elevenlabs(text, scene_index)

def _svd_generate(prompt: str, scene_index: int) -> dict:
    """Attempt to generate a video clip via a local Stable Video Diffusion server.

    Expected API (simplified pseudo):
        POST {STABLE_VIDEO_SERVER_URL}/generate {prompt: str} -> {id: str}
        GET  {STABLE_VIDEO_SERVER_URL}/status/{id} -> {status: str, url: str?}
    For now, gracefully fallback if server unreachable.
    """
    if DEV_FALLBACK_MODE:
        # In dev just reuse public sample
        return {"video_url": "https://www.w3schools.com/html/mov_bbb.mp4", "fallback": True}
    gen_endpoint = STABLE_VIDEO_SERVER_URL.rstrip('/') + '/generate'
    try:
        r = requests.post(gen_endpoint, json={"prompt": prompt}, timeout=15)
        if not r.ok:
            logging.warning("SVD generate non-OK %s: %s", r.status_code, r.text[:120])
            raise RuntimeError("svd generate failed")
        job_id = r.json().get("id")
        if not job_id:
            raise RuntimeError("svd missing id")
        status_endpoint = STABLE_VIDEO_SERVER_URL.rstrip('/') + f'/status/{job_id}'
        polls = 0
        while polls < STABLE_VIDEO_MAX_POLL:
            polls += 1
            sr = requests.get(status_endpoint, timeout=15)
            if not sr.ok:
                logging.warning("SVD status non-OK %s", sr.status_code)
                break
            payload = sr.json()
            status = payload.get("status")
            if status in {"completed", "done"}:
                url = payload.get("url") or payload.get("video_url")
                if url:
                    return {"video_url": url}
                break
            if status in {"failed", "error"}:
                logging.warning("SVD job failed: %s", payload)
                break
            import time as _t; _t.sleep(STABLE_VIDEO_POLL_INTERVAL)
    except Exception as e:
        logging.warning("SVD generation error: %s", e)
    # Fallback path: return placeholder to allow pipeline continuation
    return {"video_url": "https://www.w3schools.com/html/movie.mp4", "placeholder": True}

def _local_text_clip(narration: str, scene_index: int) -> dict:
    """Generate a short local synthetic clip with text overlay as last-resort fallback.
    Requires ffmpeg with drawtext (libfreetype). If drawtext unsupported, a plain color clip is produced.
    """
    if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
        return {"video_url": "https://www.w3schools.com/html/mov_bbb.mp4", "fallback": True}
    os.makedirs("temp", exist_ok=True)
    out_path = f"temp/synthetic_scene_{scene_index}.mp4"
    text = (narration[:50] + "…") if narration else f"Scene {scene_index+1}"
    # Try drawtext; if fails we retry without it
    base_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=720x1280:d=3",
        "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
        out_path
    ]
    try:
        subprocess.run(base_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"video_url": out_path, "generated": True}
    except Exception:
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=720x1280:d=3",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", out_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"video_url": out_path, "generated": True, "no_text": True}
        except Exception as e:
            logging.warning("Local synthetic clip failed: %s", e)
            return {"video_url": "https://www.w3schools.com/html/mov_bbb.mp4", "fallback": True}

def generate_media_assets(video_script: dict) -> list:
    """Generate media assets per scene using selected MEDIA_SOURCE.

    MEDIA_SOURCE options:
      pexels - stock footage from Pexels
      svd    - local Stable Video Diffusion server (fallbacks to placeholder if unavailable)
    """
    scenes_with_assets = []
    total = len(video_script.get("scenes", []))
    for i, scene in enumerate(video_script.get("scenes", [])):
        print(f"\nProcessing Scene {i+1}/{total} (media_source={MEDIA_SOURCE})...")
        visual_query = scene.get("visual", "")
        # VIDEO selection
        if MEDIA_SOURCE == "pexels":
            video_result = get_video_from_pexels(visual_query, i)
        elif MEDIA_SOURCE == "svd":
            prompt = visual_query or scene.get("narration", "")
            video_result = _svd_generate(prompt, i)
        else:
            video_result = {"error": f"Unsupported MEDIA_SOURCE {MEDIA_SOURCE}"}
        if "error" in video_result:
            print(f"  ⚠️ Video acquisition failed for scene {i+1}: {video_result.get('error')}")
            if ALLOW_PLACEHOLDER:
                video_result = _local_text_clip(scene.get("narration", ""), i)
            else:
                continue
        narration_text = scene.get("narration", "")
    audio_result = get_audio(narration_text, i)
        if "error" in audio_result:
            print(f"  ⚠️ Audio acquisition failed for scene {i+1}: {audio_result.get('error')}")
            if ALLOW_PLACEHOLDER:
                # Replace with silent fallback
                audio_result = {"audio_path": _generate_silent_audio(i), "placeholder": True}
            else:
                continue
        scenes_with_assets.append({
            "visual": visual_query,
            "narration": narration_text,
            "video_url": video_result["video_url"],
            "audio_path": audio_result["audio_path"],
        })
        print(f"  ✅ Scene {i+1} assets ready.")
    return scenes_with_assets
