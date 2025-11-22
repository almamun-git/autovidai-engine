import logging
import os
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict

from app.services.pipeline_runner import run_pipeline
from app.stages.stage_1_idea_engine import (
    suggest_niche_via_model,
    suggest_trending_niches,
    generate_video_idea,
)
from app.stages.stage_2_scriptwriter import build_script_prompt, run_scriptwriter
from pydantic import BaseModel
from app.config import (
    AUTOVIDAI_DEV_MODE,
    GEMINI_API_KEY,
    PEXELS_API_KEY,
    ELEVENLABS_API_KEY,
    SHOTSTACK_API_KEY,
    SHOTSTACK_STAGE,
)
import time
try:
    import shotstack_sdk
    from shotstack_sdk.api import edit_api
    from shotstack_sdk.model.clip import Clip
    from shotstack_sdk.model.track import Track
    from shotstack_sdk.model.timeline import Timeline
    from shotstack_sdk.model.output import Output
    from shotstack_sdk.model.edit import Edit
    from shotstack_sdk.model.title_asset import TitleAsset
except Exception:
    shotstack_sdk = None  # Allow app startup even if SDK missing; endpoint will report.

class PipelineRequest(BaseModel):
    niche: str
    upload: bool = False
    verbose: bool = False

class PipelineResponse(BaseModel):
    job_id: str | None = None  # placeholder for future queue integration
    stage: str | None
    final_video_url: str | None
    uploaded: bool
    error: str | None


class Stage2PromptRequest(BaseModel):
    """Request to build a default Stage 2 prompt.

    Either provide a raw niche (we will call Stage 1), or a full idea dict
    generated previously. For now we keep this minimal and flexible.
    """

    niche: str | None = None
    idea: Dict | None = None


class Stage2PromptResponse(BaseModel):
    idea: Dict
    prompt: str


class Stage2RunRequest(BaseModel):
    idea: Dict
    prompt: str
    model: str | None = None


class Stage2RunResponse(BaseModel):
    script: Dict


class SuggestResponse(BaseModel):
    niche: str | None = None  # first suggestion for backward compatibility
    niches: list[str] | None = None  # new: top 3-5 topics
    error: str | None = None

app = FastAPI(title="Automatic Video Generating AI Engine Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://automatic-video-generating-ai-engine-3.onrender.com"],  # Updated to allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/deps")
def health_deps(live: bool = Query(False, description="Perform non-destructive live checks against providers")):
    """Report dependency readiness.

    live=true performs minimal, non-destructive calls when feasible to verify credentials.
    """
    result = {"dev_mode": AUTOVIDAI_DEV_MODE}

    # Gemini
    gemini = {"ok": False, "message": "", "model": os.getenv("GEMINI_MODEL", "")}
    if not GEMINI_API_KEY:
        gemini.update(message="GEMINI_API_KEY missing")
    else:
        if live:
            model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
            try:
                r = requests.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}",
                    params={"key": GEMINI_API_KEY}, timeout=10
                )
                if r.status_code == 404:
                    # Fetch available models to suggest correct ones.
                    suggest = []
                    try:
                        rlist = requests.get(
                            "https://generativelanguage.googleapis.com/v1beta/models",
                            params={"key": GEMINI_API_KEY}, timeout=10
                        )
                        if rlist.ok:
                            data = rlist.json()
                            for m in data.get("models", [])[:10]:
                                name = m.get("name", "")
                                if "/models/" in name:
                                    name = name.split("/models/")[-1]
                                if name.startswith("gemini-2.5") or name.startswith("gemini-2.0"):
                                    suggest.append(name)
                    except Exception:
                        pass
                    gemini.update(ok=False, message=f"Model {model} 404", suggestions=suggest)
                else:
                    gemini.update(ok=r.ok, message=f"HTTP {r.status_code}")
            except Exception as e:
                gemini.update(ok=False, message=str(e))
        else:
            gemini.update(ok=True, message="Key present")
    result["gemini"] = gemini

    # Pexels
    pexels = {"ok": False, "message": ""}
    if not PEXELS_API_KEY:
        pexels.update(message="PEXELS_API_KEY missing")
    else:
        if live:
            try:
                r = requests.get(
                    "https://api.pexels.com/videos/search",
                    headers={"Authorization": PEXELS_API_KEY},
                    params={"query": "nature", "per_page": 1}, timeout=10,
                )
                pexels.update(ok=r.ok, message=f"HTTP {r.status_code}")
            except Exception as e:
                pexels.update(ok=False, message=str(e))
        else:
            pexels.update(ok=True, message="Key present")
    result["pexels"] = pexels

    # ElevenLabs
    elabs = {"ok": False, "message": ""}
    if not ELEVENLABS_API_KEY:
        elabs.update(message="ELEVENLABS_API_KEY missing")
    else:
        if live:
            try:
                r = requests.get(
                    "https://api.elevenlabs.io/v1/models",
                    headers={"xi-api-key": ELEVENLABS_API_KEY}, timeout=10
                )
                elabs.update(ok=r.ok, message=f"HTTP {r.status_code}")
            except Exception as e:
                elabs.update(ok=False, message=str(e))
        else:
            elabs.update(ok=True, message="Key present")
    result["elevenlabs"] = elabs

    # Shotstack (presence check; sandbox/stage/prod all allowed; 404/5xx status treated as neutral with guidance)
    shotstack = {"ok": False, "message": "", "stage": os.getenv("SHOTSTACK_STAGE", "v1"), "hint": "/health/shotstack for deep test"}
    if not SHOTSTACK_API_KEY:
        shotstack.update(message="SHOTSTACK_API_KEY missing")
    else:
        if live:
            try:
                # Stage or production status endpoint; tolerate 404
                stage = os.getenv("SHOTSTACK_STAGE", "v1")
                r = requests.get(f"https://api.shotstack.io/{stage}/status", timeout=10)
                if r.status_code == 404:
                    shotstack.update(ok=True, message="Status endpoint 404 (tolerated)")
                elif 500 <= r.status_code < 600:
                    # Treat server errors as neutral; advise deep check
                    shotstack.update(ok=True, message=f"Status endpoint {r.status_code} (tolerated 5xx)")
                else:
                    shotstack.update(ok=r.ok, message=f"HTTP {r.status_code}")
            except Exception as e:
                shotstack.update(ok=True, message=f"Key present; ping failed: {e}")
        else:
            shotstack.update(ok=True, message="Key present")
    result["shotstack"] = shotstack

    return result


@app.get("/providers/gemini/models")
def gemini_models():
    """Return the list of model names available to the configured GEMINI_API_KEY."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY missing")
    try:
        r = requests.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            params={"key": GEMINI_API_KEY}, timeout=15
        )
        if not r.ok:
            return {"ok": False, "status": r.status_code, "body": r.text}
        data = r.json()
        names = []
        for m in data.get("models", []):
            name = m.get("name")
            # Names sometimes include full resource path; extract final segment after '/models/'.
            if name:
                if "/models/" in name:
                    name = name.split("/models/")[-1]
                names.append(name)
        return {"ok": True, "models": names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/providers/gemini/ping")
def gemini_ping(model: str = Query(..., description="Model name to ping, e.g., gemini-1.5-flash")):
    """Ping a specific Gemini model with a GET to the models/{model} endpoint."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY missing")
    try:
        r = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}",
            params={"key": GEMINI_API_KEY}, timeout=15
        )
        return {"ok": r.ok, "status": r.status_code, "body": r.text[:400]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/health/shotstack")
def shotstack_deep(poll: bool = Query(False, description="Poll render status once after short delay")):
    """Perform a minimal Shotstack render to validate key + environment.

    Returns acceptance (render id) and optional first status poll. Uses a single title clip (1s) for minimal cost.
    """
    if not SHOTSTACK_API_KEY:
        raise HTTPException(status_code=400, detail="SHOTSTACK_API_KEY missing")
    if shotstack_sdk is None:
        raise HTTPException(status_code=500, detail="shotstack_sdk not installed")
    # Dev mode fallback: don't attempt real render
    dev_fallback = (
        os.getenv("AUTOVIDAI_DEV_MODE", "").lower() in {"1", "true", "yes"}
        or (not SHOTSTACK_API_KEY)
        or (isinstance(SHOTSTACK_API_KEY, str) and SHOTSTACK_API_KEY.startswith("dev_"))
    )
    if dev_fallback:
        return {"ok": True, "dev_fallback": True, "message": "Dev fallback active; skipping Shotstack call."}
    stage = SHOTSTACK_STAGE
    try:
        configuration = shotstack_sdk.Configuration(host="https://api.shotstack.io/" + stage)
        with shotstack_sdk.ApiClient(configuration) as api_client:
            api_client.set_default_header('x-api-key', SHOTSTACK_API_KEY)
            api_instance = edit_api.EditApi(api_client)
            # Minimal 1 second title clip
            title_asset = TitleAsset(text="Health Test", style="minimal")
            clip = Clip(asset=title_asset, start=0.0, length=1.0)
            track = Track(clips=[clip])
            timeline = Timeline(background="#000000", tracks=[track])
            # Use a low-cost standard definition render for health test
            output = Output(format="mp4", resolution="sd")
            edit = Edit(timeline=timeline, output=output)
            api_response = api_instance.post_render(edit)
            render_id = api_response['response']['id']
            status_payload = None
            if poll:
                time.sleep(2.0)
                try:
                    status_response = api_instance.get_render(render_id)
                    status_payload = {
                        "status": status_response['response']['status'],
                        "url": status_response['response'].get('url')
                    }
                except Exception as e:
                    status_payload = {"error": str(e)}
            return {
                "ok": True,
                "accepted": True,
                "render_id": render_id,
                "stage": stage,
                "polled": poll,
                "status": status_payload,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shotstack deep health failed: {e}")

@app.post("/pipeline", response_model=PipelineResponse)
def pipeline(req: PipelineRequest):
    if req.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    result = run_pipeline(req.niche, upload=req.upload)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    return PipelineResponse(
        job_id=None,
        stage=result.get("stage"),
        final_video_url=result.get("final_video_url"),
        uploaded=result.get("uploaded", False),
        error=result.get("error"),
    )


@app.post("/stage2/prompt", response_model=Stage2PromptResponse)
def stage2_prompt(req: Stage2PromptRequest):
    """Build and return the default Stage 2 prompt (and idea).

    - If an idea is provided, we trust and reuse it.
    - Otherwise, we call Stage 1 to generate an idea from the niche.
    """
    if req.idea is not None:
        idea = req.idea
    else:
        if not req.niche:
            raise HTTPException(status_code=400, detail="Either niche or idea must be provided")
        idea = generate_video_idea(req.niche)
        if isinstance(idea, dict) and idea.get("error"):
            raise HTTPException(status_code=500, detail=f"Stage 1 failed: {idea['error']}")

    prompt = build_script_prompt(idea)
    return Stage2PromptResponse(idea=idea, prompt=prompt)


@app.post("/stage2/run", response_model=Stage2RunResponse)
def stage2_run(req: Stage2RunRequest):
    """Run Stage 2 scriptwriter with a supplied prompt and optional model."""

    script = run_scriptwriter(req.idea, override_prompt=req.prompt, model=req.model)
    if (not isinstance(script, dict)) or (not script.get("scenes")) or script.get("error"):
        raise HTTPException(
            status_code=500,
            detail=script.get("error") if isinstance(script, dict) else "Invalid script returned by Stage 2",
        )
    return Stage2RunResponse(script=script)

@app.get("/files/{filename}")
def get_file(filename: str):
    """Serve files from temp/render_local for local render backend.

    Security: restrict to that directory only; no path traversal.
    """
    base_dir = os.path.abspath(os.path.join("temp", "render_local"))
    safe_path = os.path.abspath(os.path.normpath(os.path.join(base_dir, filename)))
    if not safe_path.startswith(base_dir + os.sep) and safe_path != base_dir:
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(safe_path)


@app.get("/library/videos")
def list_library_videos() -> Dict[str, List[Dict]]:
    """List generated videos stored locally in temp/render_local.

    Returns basic metadata and a playable URL via /files.
    """
    base_dir = os.path.abspath(os.path.join("temp", "render_local"))
    if not os.path.exists(base_dir):
        return {"videos": []}
    items: List[Dict] = []
    try:
        for name in os.listdir(base_dir):
            if not name.lower().endswith(".mp4"):
                continue
            path = os.path.join(base_dir, name)
            try:
                stat = os.stat(path)
                items.append({
                    "filename": name,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "url": f"/files/{name}",
                })
            except Exception:
                continue
        # Sort newest first
        items.sort(key=lambda x: x.get("mtime", 0), reverse=True)
        return {"videos": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/library/videos/{filename}")
def delete_library_video(filename: str):
    """Delete a generated video from the local library directory."""
    base_dir = os.path.abspath(os.path.join("temp", "render_local"))
    safe_path = os.path.abspath(os.path.normpath(os.path.join(base_dir, filename)))
    if not safe_path.startswith(base_dir + os.sep) and safe_path != base_dir:
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        os.remove(safe_path)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/suggest", response_model=SuggestResponse)
def suggest(count: int = Query(5, ge=3, le=8, description="Number of topics to suggest (3-8)")):
    """Return multiple suggested trending topics (3-5 default) generated by the model.

    Backward compatible: includes 'niche' as the first element.
    """
    topics = suggest_trending_niches(count)
    if not topics:
        # Never fail the UX — provide deterministic stub list
        topics = [
            "AI productivity hacks",
            "indoor plants care",
            "morning routine optimization",
            "budget meal prep",
            "coding interview tips",
        ][:max(3, min(count, 8))]
    return SuggestResponse(niche=topics[0], niches=topics)
