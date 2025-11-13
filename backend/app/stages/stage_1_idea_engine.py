import json
import requests
import re
from app.config import GEMINI_API_KEY

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"

def generate_video_idea(niche: str) -> dict:
    print("--- Stage 1: Idea Engine ---")
    print(f"Received niche: {niche}")

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
    print("Generating idea with Gemini AI...")
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": master_prompt}]}]}

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
        response_data = response.json()
        text_content = response_data['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\{.*\}', text_content, re.DOTALL)
        if not json_match:
            raise json.JSONDecodeError("No JSON object found in response", text_content, 0)
        json_text = json_match.group(0)
        video_idea = json.loads(json_text)
        print("✅ Idea generated successfully.")
        return video_idea
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Gemini API: {e}")
        return {"error": "API request failed", "details": str(e)}
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"❌ Error parsing Gemini response: {e}")
        print(f"Raw Response Text: {locals().get('text_content', 'Not available')}")
        return {"error": "Could not parse API response", "details": str(e)}


def suggest_niche_via_model() -> str | None:
    """Ask the model to suggest a single concise, safe niche/topic.

    Returns the suggested niche string or None on failure.
    """
    prompt = (
        "Suggest one concise, safe niche/topic for a short-form social media video. "
        "Return exactly one short phrase (no punctuation), for example: AI productivity"
    )
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=20)
        resp.raise_for_status()
        resp_data = resp.json()
        text = resp_data['candidates'][0]['content']['parts'][0]['text']
        # pick first non-empty line and sanitize
        first = next((line.strip() for line in text.splitlines() if line.strip()), None)
        if not first:
            return None
        # remove punctuation except hyphens and spaces
        safe = re.sub(r"[^\w\s-]", "", first).strip()
        return safe if safe else None
    except Exception as e:
        print(f"❌ Error suggesting niche via model: {e}")
        return None
