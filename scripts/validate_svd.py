import os, sys, json, pathlib, time
sys.path.append('backend')
# Set env vars for test run
os.environ['MEDIA_SOURCE'] = 'svd'
os.environ['FAST_MODE'] = '1'
os.environ['RENDER_BACKEND'] = 'local'
os.environ.setdefault('GEMINI_MODEL','gemini-2.5-flash')
from app.services.pipeline_runner import run_pipeline

print('[validate] Starting pipeline with MEDIA_SOURCE=svd FAST_MODE=1 RENDER_BACKEND=local')
result = run_pipeline('indoor plants care', upload=False)
print('[validate] Pipeline result:')
print(json.dumps(result, indent=2))
# Inspect scene asset summary, prefer enriched assets list
assets = result.get('assets')
if not assets:
    # fallback to script scenes (un-enriched)
    scenes = result.get('script', {}).get('scenes', [])
    assets = [
        {
            'i': i,
            'video_url': s.get('video_url'),
            'audio_path': s.get('audio_path'),
            'narration_len': len((s.get('narration') or '').split()),
        }
        for i, s in enumerate(scenes)
    ]
else:
    # normalize enriched assets
    assets = [
        {
            'i': i,
            'video_url': s.get('video_url'),
            'audio_path': s.get('audio_path'),
            'narration_len': len((s.get('narration') or '').split()),
        }
        for i, s in enumerate(assets)
    ]
print('[validate] Scene asset summary (video_url, audio_path, narration_len):')
print(json.dumps(assets, indent=2))
# Check final video size if local rendered
fv = result.get('final_video_url')
if fv and os.path.exists(fv):
    sz = os.path.getsize(fv)
    print(f"[validate] Final video exists: {fv} ({sz} bytes)")
else:
    print('[validate] Final video not found locally or using remote URL.')
