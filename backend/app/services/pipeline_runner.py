import json
import logging
from dotenv import load_dotenv

# Reuse existing stage modules from the root project
from app.stages.stage_1_idea_engine import generate_video_idea
from app.stages.stage_2_scriptwriter import generate_video_script
from app.stages.stage_3_media_engine import generate_media_assets
from app.stages.stage_4_renderer import render_video
from app.stages.stage_5_distributor import upload_video_to_youtube
import os, time, shutil, re


def run_pipeline(niche: str, upload: bool = False) -> dict:
    """
    Orchestrate the entire video creation pipeline from idea to publish.
    Returns a structured result for programmatic use by the API layer.
    """
    load_dotenv()
    logging.info("Starting pipeline — niche=%s", niche)

    result = {
        "niche": niche,
        "stage": None,
        "idea": None,
        "script": None,
        "assets": None,
        "render": None,
        "final_video_url": None,
        "uploaded": False,
        "error": None,
    }

    try:
        # Stage 1: Idea
        result["stage"] = "idea"
        idea = generate_video_idea(niche)
        if isinstance(idea, dict) and idea.get("error"):
            raise RuntimeError(f"Stage 1 failed: {idea['error']}")
        result["idea"] = idea
        logging.info("Stage 1 complete")
        logging.debug("IDEA: %s", json.dumps(idea, indent=2))

        # Stage 2: Script
        result["stage"] = "script"
        script = generate_video_script(idea)
        if (not isinstance(script, dict)) or (not script.get("scenes")) or script.get("error"):
            raise RuntimeError(
                f"Stage 2 failed: {script.get('error') if isinstance(script, dict) else 'invalid script'}"
            )
        result["script"] = script
        logging.info("Stage 2 complete")
        logging.debug("SCRIPT: %s", json.dumps(script, indent=2))

        # Stage 3: Assets
        result["stage"] = "assets"
        assets = generate_media_assets(script)
        if not assets:
            raise RuntimeError("Stage 3 failed: no assets generated")
        result["assets"] = assets
        logging.info("Stage 3 complete")

        # Stage 4: Render
        result["stage"] = "render"
        title = idea.get("title", "AI Generated Video") if isinstance(idea, dict) else "AI Generated Video"
        render_result = render_video(assets, title)
        if (not isinstance(render_result, dict)) or render_result.get("error") or ("final_video_url" not in render_result):
            raise RuntimeError(
                f"Stage 4 failed: {render_result.get('error') if isinstance(render_result, dict) else 'invalid render result'}"
            )
        result["render"] = render_result
        result["final_video_url"] = render_result["final_video_url"]
        logging.info("Stage 4 complete — final_url=%s", result["final_video_url"])

        # Append video to local library with a unique name (if local render)
        try:
            if isinstance(render_result, dict) and render_result.get("local") and os.path.exists(result["final_video_url"] or ""):
                base_dir = os.path.join("temp", "render_local")
                os.makedirs(base_dir, exist_ok=True)
                # Build a slug from the title
                slug = re.sub(r"[^a-z0-9]+", "-", (title or "video").lower()).strip("-")
                ts = time.strftime("%Y%m%d-%H%M%S")
                target_name = f"{slug}-{ts}.mp4"
                target_path = os.path.join(base_dir, target_name)
                shutil.copyfile(result["final_video_url"], target_path)
                # Include library url for convenience
                result["library_file"] = target_name
                result["library_url"] = f"/files/{target_name}"
        except Exception as e:
            logging.warning("Could not archive video to library: %s", e)

        # Stage 5: Upload (optional)
        if upload:
            result["stage"] = "upload"
            video_title = title
            video_description = (
                idea.get("description", "This video was generated automatically.")
                if isinstance(idea, dict)
                else "This video was generated automatically."
            )
            upload_video_to_youtube(result["final_video_url"], video_title, video_description)
            result["uploaded"] = True
            logging.info("Stage 5 complete (uploaded)")

        result["stage"] = "done"
        logging.info("Pipeline finished successfully")
        return result

    except Exception as e:
        logging.exception("Pipeline failed at stage: %s", result.get("stage"))
        result["error"] = str(e)
        return result
