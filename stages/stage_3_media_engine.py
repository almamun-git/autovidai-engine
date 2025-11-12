import os
import requests
from config import PEXELS_API_KEY, ELEVENLABS_API_KEY

def get_video_from_pexels(query: str, scene_index: int) -> dict:
    """
    Fetches a relevant video clip from Pexels based on a search query.
    """
    print(f"  - Searching Pexels for video: '{query}'")
    
    headers = {
        'Authorization': PEXELS_API_KEY
    }
    
    params = {
        'query': query,
        'per_page': 1,
        'orientation': 'portrait'  # For vertical/9:16 videos
    }
    
    try:
        response = requests.get('https://api.pexels.com/videos/search', headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('videos') and len(data['videos']) > 0:
            video = data['videos'][0]
            # Get the highest quality video file available
            video_files = video.get('video_files', [])
            
            # Prefer HD portrait orientation
            best_video = None
            for vf in video_files:
                if vf.get('quality') == 'hd' and vf.get('width', 0) < vf.get('height', 0):
                    best_video = vf
                    break
            
            # Fallback to any HD video
            if not best_video:
                for vf in video_files:
                    if vf.get('quality') == 'hd':
                        best_video = vf
                        break
            
            # Final fallback to first video file
            if not best_video and video_files:
                best_video = video_files[0]
            
            if best_video:
                video_url = best_video.get('link')
                print(f"    -> ✅ Found Pexels video: {video_url}")
                return {"video_url": video_url}
        
        print(f"    -> ⚠️ No suitable video found on Pexels for query: '{query}'")
        return {"error": "No video found on Pexels"}
        
    except requests.RequestException as e:
        print(f"    -> ❌ Pexels API Error: {e}")
        return {"error": "Pexels API request failed", "details": str(e)}


def get_audio_from_elevenlabs(text: str, scene_index: int) -> dict:
    """
    Generates TTS audio using ElevenLabs API.
    """
    print(f"  - Generating TTS audio for: '{text[:50]}...'")
    
    # Using ElevenLabs' default voice (Rachel)
    voice_id = "21m00Tcm4TlvDq8ikWAM"
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': ELEVENLABS_API_KEY
    }
    
    payload = {
        'text': text,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Save the audio file locally
        os.makedirs('temp', exist_ok=True)
        audio_filename = f"temp/audio_scene_{scene_index}.mp3"
        
        with open(audio_filename, 'wb') as f:
            f.write(response.content)
        
        print(f"    -> ✅ TTS audio saved: {audio_filename}")
        return {"audio_path": audio_filename}
        
    except requests.RequestException as e:
        print(f"    -> ❌ ElevenLabs API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"      -> Response: {e.response.text}")
        return {"error": "ElevenLabs API request failed", "details": str(e)}


def generate_media_assets(video_script: dict) -> list:
    """
    Processes all scenes and fetches video clips from Pexels and generates
    TTS audio from ElevenLabs for each scene.
    """
    scenes_with_assets = []
    
    for i, scene in enumerate(video_script["scenes"]):
        print(f"\nProcessing Scene {i+1}/{len(video_script['scenes'])}...")
        
        # Get video clip from Pexels
        visual_query = scene.get("visual", "")
        video_result = get_video_from_pexels(visual_query, i)
        
        if "error" in video_result:
            print(f"  ⚠️ Skipping scene {i+1} due to video error.")
            continue
        
        # Get TTS audio from ElevenLabs
        narration_text = scene.get("narration", "")
        audio_result = get_audio_from_elevenlabs(narration_text, i)
        
        if "error" in audio_result:
            print(f"  ⚠️ Skipping scene {i+1} due to audio error.")
            continue
        
        # Combine everything into the scene
        scene_with_assets = {
            "visual": visual_query,
            "narration": narration_text,
            "video_url": video_result["video_url"],
            "audio_path": audio_result["audio_path"]
        }
        
        scenes_with_assets.append(scene_with_assets)
        print(f"  ✅ Scene {i+1} assets ready.")
    
    return scenes_with_assets

