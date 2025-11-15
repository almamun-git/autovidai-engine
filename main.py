import argparse
import logging
from backend.app.services.pipeline_runner import run_pipeline


def configure_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")


def cli():
    parser = argparse.ArgumentParser(description="Run pipeline (CLI)")
    parser.add_argument("--niche", type=str, default="Stoicism", help="Single-word niche, e.g., 'Stoicism'")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube after rendering")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    configure_logging(args.verbose)
    result = run_pipeline(args.niche, upload=args.upload)
    if result.get("error"):
        logging.error("Pipeline failed: %s", result["error"]) 
        raise SystemExit(1)
    print(f"Final video URL: {result.get('final_video_url')}")


if __name__ == "__main__":
    cli()





