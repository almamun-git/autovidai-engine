import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.services.pipeline_runner import run_pipeline

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

app = FastAPI(title="AutoVidAI Backend", version="0.1.0")

@app.on_event("startup")
def startup():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@app.get("/health")
def health():
    return {"status": "ok"}

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
