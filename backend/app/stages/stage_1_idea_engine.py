import json
import requests
import re
import logging
import os
from app.config import GEMINI_API_KEY
from typing import List

# Allow overriding the Gemini model via env; default to a model commonly available per /providers/gemini/models.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Build endpoint (v1beta generateContent). "-latest" occasionally returns 404; use explicit model.
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

# Detect dev / stub mode (no real key or intentionally using a placeholder) to enable graceful fallbacks.
DEV_FALLBACK_MODE = (
    os.getenv("AUTOVIDAI_DEV_MODE", "").lower() in {"1", "true", "yes"}
    or not GEMINI_API_KEY
    or (isinstance(GEMINI_API_KEY, str) and GEMINI_API_KEY.startswith("dev_"))
    or (isinstance(GEMINI_MODEL, str) and GEMINI_MODEL.startswith("stub_"))
)

def generate_video_idea(niche: str) -> dict:
    logging.info("--- Stage 1: Idea Engine ---")
    logging.info("Received niche: %s", niche)

    # Validate input — do not proceed with an empty or placeholder niche
    if not niche or not str(niche).strip():
        print("❌ Error: missing required 'niche' parameter")
        return {"error": "Missing required parameter: niche"}

    # Use the provided niche value (trim whitespace) and ensure prompt spacing is correct.
    niche_clean = str(niche).strip()
    master_prompt = f"""
    You're a social media expert who knows how to make short-form videos go viral.
    Your job is to come up with a complete video idea for the niche: {niche_clean}. Keep the tone natural, engaging, and attention-grabbing — something that feels exciting and made for social media.
    Respond with only one minified JSON object — no line breaks, no markdown, no extra explanation. Make sure your response follows this format exactly:
    {{
        "title": "A short, catchy, title-case title for the video.",
        "hook": "A strong, one-sentence opening line to grab the viewer's attention.",
        "description": "A brief description for the social media post, including 3-5 relevant hashtags.",
        "points": [
            "A list of 3 to 5 key points or facts that will be the main content of the video."
        ],
        "cta": "A clear, short call-to-action for the end of the video."
    }}
    Just return the JSON — nothing else.
    """
    # If we are in dev fallback mode, skip remote call and return deterministic stub.
    if DEV_FALLBACK_MODE:
        logging.warning("Gemini dev fallback mode active — returning stub idea (no external API call).")
        return _stub_idea(niche_clean)

    logging.info("Calling Gemini model '%s' for idea generation...", GEMINI_MODEL)
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": master_prompt}]}]}

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        response_data = response.json()
        text_content = response_data['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\{.*\}', text_content, re.DOTALL)
        if not json_match:
            raise json.JSONDecodeError("No JSON object found in response", text_content, 0)
        json_text = json_match.group(0)
        video_idea = json.loads(json_text)
        logging.info("✅ Idea generated successfully.")
        return video_idea
    except requests.exceptions.RequestException as e:
        logging.error("❌ Error calling Gemini API: %s", e)
        # Graceful fallback — still produce a usable idea so pipeline can continue.
        return _stub_idea(niche_clean)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logging.error("❌ Error parsing Gemini response: %s", e)
        logging.debug("Raw Response Text: %s", locals().get('text_content', 'Not available'))
        return _stub_idea(niche_clean)


def suggest_niche_via_model() -> str | None:
    """Ask the model to suggest a single concise, safe niche/topic.

    Returns the suggested niche string or None on failure. Falls back to a stub niche in dev mode.
    """
    if DEV_FALLBACK_MODE:
        logging.warning("Dev fallback active for suggest_niche_via_model — returning stub niche.")
        return "ai productivity"

    prompt = (
        "Suggest one concise, safe niche/topic for a short-form social media video. "
        "Return exactly one short phrase (no punctuation), for example: AI productivity"
    )
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        resp_data = resp.json()
        text = resp_data['candidates'][0]['content']['parts'][0]['text']
        first = next((line.strip() for line in text.splitlines() if line.strip()), None)
        if not first:
            return None
        safe = re.sub(r"[^\w\s-]", "", first).strip()
        return safe if safe else None
    except Exception as e:
        logging.error("❌ Error suggesting niche via model: %s", e)
        return None


def suggest_trending_niches(count: int = 5) -> List[str]:
    """Suggest 3-5 concise, safe trending topics for short-form videos.

    Attempts Gemini first; falls back to deterministic stub list when unavailable.
    Returns a list of strings (length between 3 and `count`).
    """
    # Normalize desired count between 3 and 8
    n = max(3, min(count, 8))
    if DEV_FALLBACK_MODE:
        logging.warning("Dev fallback active — returning stub trending topics.")
        stub = [
            "AI productivity hacks",
            "indoor plants care",
            "morning routine optimization",
            "budget meal prep",
            "coding interview tips",
            "healthy habit building",
            "creator monetization tips",
            "shorts editing tricks",
        ]
        import random
        random.shuffle(stub)
        return stub[:n]

    prompt = (
        "List top trending short-form video topics. "
        f"Return ONLY a compact JSON array of {n} strings, no markdown, no extra text. "
        "Keep each item short (3-5 words), safe, and platform-appropriate."
    )
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        text = data['candidates'][0]['content']['parts'][0]['text']
        # Prefer a JSON array; fallback to line-based parsing
        arr_match = re.search(r"\[.*\]", text, re.DOTALL)
        if arr_match:
            raw = arr_match.group(0)
            arr = json.loads(raw)
            topics = [
                re.sub(r"[^\w\s-]", "", str(x)).strip()
                for x in arr
                if str(x).strip()
            ]
            topics = [t for t in topics if t]
            return topics[:n] if topics else []
        # Fallback: split lines
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        topics: List[str] = []
        for ln in lines:
            # strip bullets, punctuation
            t = re.sub(r"^[\-\*\d\.]+\s*", "", ln)
            t = re.sub(r"[^\w\s-]", "", t).strip()
            if t:
                topics.append(t)
            if len(topics) >= n:
                break
        # If model returned a single comma-separated line, split by commas/semicolons/pipes
        if len(topics) <= 1 and lines:
            single = lines[0]
            segs = re.split(r"[,;\|]", single)
            split_topics = []
            for s in segs:
                s2 = re.sub(r"[^\w\s-]", "", s).strip()
                if s2:
                    split_topics.append(s2)
            if split_topics:
                topics = split_topics
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for t in topics:
            if t.lower() in seen:
                continue
            seen.add(t.lower())
            deduped.append(t)
        return deduped[:n]
    except Exception as e:
        logging.error("❌ Error suggesting trending topics: %s", e)
        # Stub fallback
        stub = [
            "AI productivity hacks",
            "indoor plants care",
            "morning routine optimization",
            "budget meal prep",
            "coding interview tips",
            "healthy habit building",
            "creator monetization tips",
            "shorts editing tricks",
        ]
        import random
        random.shuffle(stub)
        return stub[:n]


def _stub_idea(niche: str, error: str | None = None) -> dict:
    """Return a deterministic stub idea structure so downstream stages can proceed.

    Includes an 'fallback' flag and optionally the original error message for observability.
    """
    stub = {
        "title": f"Quick Tips About {niche.title()}",
        "hook": f"Stop scrolling – {niche.lower()} hack you need today!",
        "description": f"A short-form video about {niche}. #AI #Tips #Learning",
        "points": [
            f"Intro to {niche} in one sentence",
            f"Key benefit of {niche}",
            f"Common mistake people make",
            f"Pro tip to improve results",
        ],
        "cta": "Follow for more quick wins!",
        "fallback": True,
    }
    # Do not include an 'error' field to avoid failing the pipeline; log instead.
    if error:
        logging.debug("Stub idea used due to error: %s", error)
    return stub
