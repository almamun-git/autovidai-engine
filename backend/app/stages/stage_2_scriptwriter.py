import json
import re
import requests
import logging
import os
from app.config import GEMINI_API_KEY

# Allow overriding model; default to a model commonly available to AI Studio keys.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key="
    + GEMINI_API_KEY
)

DEV_FALLBACK_MODE = (
    os.getenv("AUTOVIDAI_DEV_MODE", "").lower() in {"1", "true", "yes"}
    or not GEMINI_API_KEY
    or (isinstance(GEMINI_API_KEY, str) and GEMINI_API_KEY.startswith("dev_"))
    or (isinstance(GEMINI_MODEL, str) and GEMINI_MODEL.startswith("stub_"))
)


def build_script_prompt(video_idea: dict) -> str:
    """Build the default Stage 2 scriptwriter prompt from a video_idea.

    Separated so the frontend can:
    - inspect this prompt
    - allow users to edit it
    - send an override back to the backend
    """
    return f"""You are DeepResearch-ScriptWriter, an advanced reasoning agent specialized in high-retention short-form video scripting for TikTok, Reels, and YouTube Shorts. Use deep analysis, narrative optimization, and social-media algorithm insights to convert the following concept into a fully structured, viral-ready script.

    Input Concept:
    - Title: {video_idea['title']}
    - Hook: {video_idea['hook']}
    - Key Points: {', '.join(video_idea['points'])}
    - Call to Action: {video_idea['cta']}

    Guidelines:
    1. Leverage the strongest emotional and curiosity triggers from the concept to hook viewers.
    2. Maintain a fast, punchy, dynamic pacing throughout the script.
    3. Turn each Key Point into its own scene, and make each scene visually distinct to maximize contrast and novelty.
    4. Describe visuals vividly with clear action/motion, suitable for AI generation (imagine a cinematic clip for each scene).
    5. Keep narration lines sharp, impactful, and under 15 words each.

    Output Instructions:
    1. Produce exactly 5 to 7 scenes total.
    2. Scene 1 must open with the provided Hook as its narration.
    3. Scenes 2-{{n-1}}: use each Key Point in order as the basis for each middle scene, crafting them into creative high-retention micro-stories.
    4. Final Scene: end with the Call to Action as the narration, delivered energetically.
    5. For every scene, include:
    - "visual": A vivid, cinematic description of the scene (what the viewer sees).
    - "narration": An engaging voiceover line (max 15 words).
    6. No filler, no generic advice, no repeated lines. The tone should be fast-paced, modern, and feel native to the platform.
    7. Response Format – Provide the output as a single valid JSON object with the structure:
    {{"scenes": [{{"visual": "...", "narration": "..."}}, ...]}}
    - Do NOT include any markdown, code blocks, or explanatory text. Only output the JSON.
    - The JSON should be minified (no unnecessary line breaks or spaces).
    - The response must contain nothing outside the JSON (no intro or comments, just the JSON object).

    Remember: Respond only with the JSON object as specified, and ensure it follows the format and requirements above.
    """


def run_scriptwriter(
    video_idea: dict,
    override_prompt: str | None = None,
    model: str | None = None,
) -> dict:
    """Core Stage 2 runner.

    - Builds the default prompt (unless override_prompt is provided).
    - Calls Gemini with the selected model (or default GEMINI_MODEL).
    - Returns the parsed script dict.
    """
    logging.info("--- Stage 2: Scriptwriter ---")
    logging.info("Received video idea. Generating script...")

    prompt = override_prompt if override_prompt is not None else build_script_prompt(video_idea)
    selected_model = model or GEMINI_MODEL
    api_url = GEMINI_API_URL_TEMPLATE.format(model=selected_model)

    # Dev fallback: synthesize a deterministic script without external calls.
    if DEV_FALLBACK_MODE:
        logging.warning("Dev fallback active for Stage 2 — returning stub script.")
        return _stub_script(video_idea)

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
        },
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        video_script = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        parsed_script = json.loads(video_script)
        logging.info("✅ Script generated successfully.")
        return parsed_script
    except requests.exceptions.HTTPError as http_err:
        logging.error("❌ HTTP Error in Stage 2: %s", http_err)
        logging.debug("Response body: %s", getattr(response, "text", ""))
        return _stub_script(video_idea)
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logging.error("❌ Error parsing JSON in Stage 2: %s", e)
        if "response" in locals():
            try:
                logging.debug(
                    "Raw response text: %s",
                    response.json()["candidates"][0]["content"]["parts"][0]["text"],
                )
            except Exception:
                pass
        return _stub_script(video_idea)
    except Exception as e:
        logging.error("❌ An unexpected error occurred in Stage 2: %s", e)
        return _stub_script(video_idea)


def generate_video_script(video_idea: dict) -> dict:
    """Backwards-compatible entry point used by the pipeline.

    For now this simply calls run_scriptwriter() with the default prompt
    and default model. New APIs can call run_scriptwriter(...) directly
    with an override_prompt and/or model.
    """
    return run_scriptwriter(video_idea)


def _stub_script(video_idea: dict, error: str | None = None) -> dict:
    """Return a minimal viable script with 5 scenes for downstream processing."""
    title = video_idea.get("title", "AI Video")
    hook = video_idea.get("hook", "Here's something cool!")
    points = video_idea.get("points") or [
        "What it is",
        "Why it matters",
        "Common mistake",
        "Pro tip",
    ]
    scenes = []
    scenes.append({
        "visual": f"Dynamic macro shot related to {title}",
        "narration": hook,
    })
    for p in points[:4]:
        scenes.append({
            "visual": f"B-roll illustrating: {p}",
            "narration": p if len(p) <= 15 else p.split('.')[0][:60],
        })
    scenes.append({
        "visual": "Bold text overlay and logo animation",
        "narration": video_idea.get("cta", "Follow for more!"),
    })
    if error:
        logging.debug("Stub script used due to error: %s", error)
    return {"scenes": scenes, "fallback": True}
