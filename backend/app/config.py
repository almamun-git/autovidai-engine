import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import logging

# Load .env from project root even when running from backend/
load_dotenv(find_dotenv(usecwd=True) or Path(__file__).resolve().parents[2] / '.env')

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
SHOTSTACK_API_KEY = os.getenv("SHOTSTACK_API_KEY")
# Render backend selection: 'shotstack' (default) or 'local'
RENDER_BACKEND = os.getenv("RENDER_BACKEND", "shotstack").lower().strip()
# Media source selection for Stage 3: 'pexels' (stock) or 'svd' (Stable Video Diffusion local server)
MEDIA_SOURCE = os.getenv("MEDIA_SOURCE", "pexels").lower().strip()
# TTS source selection: 'elevenlabs' (API) or 'local' (offline engine)
TTS_SOURCE = os.getenv("TTS_SOURCE", "elevenlabs").lower().strip()
# Optional self-hosted Stable Video Diffusion server URL
STABLE_VIDEO_SERVER_URL = os.getenv("STABLE_VIDEO_SERVER_URL", "http://127.0.0.1:7860")
STABLE_VIDEO_POLL_INTERVAL = float(os.getenv("STABLE_VIDEO_POLL_INTERVAL", "3"))  # seconds
STABLE_VIDEO_MAX_POLL = int(os.getenv("STABLE_VIDEO_MAX_POLL", "40"))  # ~2 minutes default
# Use 'v1' for production, 'stage' for Shotstack staging environments
_raw_stage = os.getenv("SHOTSTACK_STAGE", "v1").lower().strip()
if _raw_stage in {"stage", "staging", "sandbox", "dev"}:
    SHOTSTACK_STAGE = "stage"
elif _raw_stage in {"prod", "production", "live", "v1"}:
    SHOTSTACK_STAGE = "v1"
else:
    # Fallback: trust user-provided value (advanced custom envs)
    SHOTSTACK_STAGE = _raw_stage or "v1"

# Dev mode allows running without real keys; stages will provide fallbacks.
AUTOVIDAI_DEV_MODE = 0

if not AUTOVIDAI_DEV_MODE and RENDER_BACKEND != "local":
    # In non-dev mode, enforce presence of all keys unless using local renderer (which bypasses Shotstack and can run w/o SHOTSTACK key).
    if not all([GEMINI_API_KEY, PEXELS_API_KEY, ELEVENLABS_API_KEY, SHOTSTACK_API_KEY]):
        raise ValueError("One or more API keys are missing. Please check your .env file or enable AUTOVIDAI_DEV_MODE or set RENDER_BACKEND=local.")

# Basic sanity: MEDIA_SOURCE must be one of supported options
if MEDIA_SOURCE not in {"pexels", "svd"}:
    logging.warning(f"Unsupported MEDIA_SOURCE '{MEDIA_SOURCE}' - falling back to 'pexels'")
    MEDIA_SOURCE = "pexels"
if TTS_SOURCE not in {"elevenlabs", "local"}:
    logging.warning(f"Unsupported TTS_SOURCE '{TTS_SOURCE}' - falling back to 'elevenlabs'")
    TTS_SOURCE = "elevenlabs"
