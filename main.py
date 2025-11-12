import json
from stages.stage_1_idea_engine import generate_video_idea
from stages.stage_2_scriptwriter import generate_video_script
from stages.stage_3_media_engine import generate_media_assets
from stages.stage_4_renderer import render_video
from stages.stage_5_distributor import upload_video_to_youtube

def run_pipeline():
    """
    Orchestrates the entire video creation pipeline from idea to publish.
    """
    print("🚀 Starting AutoVidAI Pipeline...")
    niche = "Stoicism"

    # Stage 1: Content Strategy (Idea Engine)
    video_idea = generate_video_idea(niche)
    
    if "error" in video_idea:
        print("❗️ Pipeline stopped in Stage 1.")
        return
    
    print("\n" + "="*50)
    print("           GENERATED VIDEO IDEA")
    print("="*50)
    print(json.dumps(video_idea, indent=4))
    print("\n✅ Stage 1 Complete.\n" + "-"*50)

    # Stage 2: Scripting (Scriptwriter)
    video_script = generate_video_script(video_idea)
    
    if "error" in video_script or not video_script.get("scenes"):
        print("❗️ Pipeline stopped in Stage 2.")
        return

    print("\n" + "="*50)
    print("           GENERATED VIDEO SCRIPT")
    print("="*50)
    print(json.dumps(video_script, indent=4))
    print("\n✅ Stage 2 Complete.\n" + "-"*50)

    # Stage 3: Asset Generation (Media Engine)
    print("\n--- Stage 3: Media Engine (Pexels + ElevenLabs) ---")
    scenes_with_assets = generate_media_assets(video_script)
    
    if not scenes_with_assets:
        print("❗️ Pipeline stopped in Stage 3.")
        return
    
    print("\n✅ Stage 3 Complete.\n" + "-"*50)

    # Stage 4: Rendering (Video Assembly)
    render_result = render_video(scenes_with_assets, video_idea.get("title", "AI Generated Video"))
    
    if "error" in render_result:
        print("❗️ Pipeline stopped in Stage 4.")
        return
    
    print("\n✅ Stage 4 Complete.\n" + "-"*50)

    # Stage 5: Distribution (YouTube Upload - Optional)
    final_video_url = render_result['final_video_url']
    video_title = video_idea.get('title', 'AI Generated Video')
    video_description = video_idea.get('description', 'This video was generated automatically.')
    
    print(f"\n🎥 Final Video URL: {final_video_url}")
    print("\nTo upload to YouTube, uncomment the line below:")
    # upload_video_to_youtube(final_video_url, video_title, video_description)

    print("\n🎉 AutoVidAI Pipeline Finished Successfully! 🎉")


if __name__ == "__main__":
    run_pipeline()





