# Automatic Video Generating AI Engine

**Automatic Video Generating AI Engine** (formerly AutoVidAI) is a headless, API-first orchestration engine built in Python to fully automate the production of short-form social media videos. The goal is to create a fully autonomous, "set and forget" content pipeline by composing a series of micro-tasks powered by best-in-class APIs.

The engine currently operates as a **5-stage workflow**, passing structured JSON payloads between each stage to maintain state.

---

## 🚀 How It Works

The system takes a single-word niche (e.g., "Stoicism") and executes the following automated pipeline:

### **Stage 1: Content Strategy (Idea Engine)**
- Uses **Google's Gemini API** to brainstorm a structured, potentially viral video concept based on the input niche.

### **Stage 2: Scripting (Scriptwriter)**
- Takes the concept from Stage 1 and uses further LLM processing to expand it into a detailed, scene-by-scene script optimized for short-form video.

### **Stage 3: Asset Generation (Media Engine)**
- Makes parallel API calls to source all necessary media.
- Fetches relevant stock video clips from the **Pexels API** (default).
- (Experimental) Generates AI video clips via a **self-hosted Stable Video Diffusion** server when `MEDIA_SOURCE=svd`.
- Generates narration via **ElevenLabs API** or local offline TTS when `TTS_SOURCE=local` (pyttsx3). Falls back to generated silence if unavailable.

### **Stage 4: Rendering (Video Assembly)**
- Assembles the final edit by sending the script, video assets, and audio assets to the **Shotstack Video API** for programmatic, cloud-based rendering.

### **Stage 5: Distribution (In Development)**
- The final stage will be responsible for programmatically uploading the finished video to social media platforms.

---

## 🛠️ Tech Stack & Architecture

This project is a demonstration of API orchestration and building a resilient, multi-step automated workflow.

**Orchestration & Logic:** Python  
**Core Libraries:** `requests`, `python-dotenv`, `shotstack-sdk`

### **AI & Content APIs:**
- **Google Gemini API:** For idea generation and scripting.
- **Pexels API:** For high-quality stock video footage.
- **ElevenLabs API:** For realistic text-to-speech voiceover synthesis.

### **Rendering Backends:**
- **Shotstack API (cloud)**: Programmatic editing & high-quality rendering.
- **Local FFmpeg (free fallback)**: Set `RENDER_BACKEND=local` to bypass Shotstack and stitch scenes on your machine (lower quality, minimal features, zero cost).

### **Media Sources (Stage 3):**
### **TTS Sources (Narration):**
| Source | Env Setting | Pros | Cons |
|--------|-------------|------|------|
| ElevenLabs API | `TTS_SOURCE=elevenlabs` (default) | High quality voices | Requires API key, quota/cost |
| Local TTS (pyttsx3) | `TTS_SOURCE=local` | Free, offline | Robotic voice, limited expressiveness |

Set `TTS_SOURCE=local` to eliminate external TTS costs. Generated WAV is converted to MP3 if `ffmpeg` is installed; otherwise WAV is used directly.

### Local Offline TTS

To enable offline narration generation:
```
export TTS_SOURCE=local
pip install pyttsx3
```
Ensure a speech synthesis backend is available (on macOS pyttsx3 uses NSSpeechSynthesizer). If ffmpeg is installed the WAV will be converted to MP3 automatically.

| Source | Env Setting | Purpose | Fallbacks |
|--------|------------|---------|-----------|
| Pexels | `MEDIA_SOURCE=pexels` (default) | Stock footage retrieval | Placeholder sample video if no match or API error |
| Stable Video Diffusion (local) | `MEDIA_SOURCE=svd` | AI‑generated motion clip per scene | Placeholder sample or synthetic text clip if server unavailable |

Experimental SVD mode expects a local server exposing a minimal API:
```
POST /generate { "prompt": "text" } -> { "id": "job123" }
GET  /status/job123 -> { "status": "completed", "url": "http://.../clip.mp4" }
```
Environment variables influencing this flow:
```
MEDIA_SOURCE=svd
STABLE_VIDEO_SERVER_URL=http://127.0.0.1:7860
STABLE_VIDEO_POLL_INTERVAL=3
STABLE_VIDEO_MAX_POLL=40
```
If generation fails or times out, a local synthetic clip (black background + text) or public sample video is substituted to keep the pipeline resilient.

---

## ⚙️ Setup and Installation

To get this project running locally, follow these steps.

### **Quick Setup (Recommended)**

Run the setup script that automates the entire setup process:

```bash
./setup.sh
```

This will:
- Check for Python 3
- Create a virtual environment
- Install all dependencies
- Create a `.env` file from the template
- Set up the temp directory

### **Manual Setup**

If you prefer to set up manually, follow these steps:

### **1. Clone the Repository:**
```bash
git clone https://github.com/mamun-apu/autovidai-engine.git
cd autovidai-engine
```

### **2. Create and Activate a Virtual Environment:**
This project requires a virtual environment to manage dependencies.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it (on macOS/Linux)
source venv/bin/activate
```

### **3. Install Dependencies:**
Install all the required Python packages.

```bash
pip3 install -r requirements.txt
```

### **4. Set Up Environment Variables:**
You will need API keys from all the services used in this project.

1. Create a `.env` file in the root of the project:
   ```bash
   touch .env
   ```

2. Add the following lines to your `.env` file, replacing the placeholders with your actual keys:
   ```env
   GEMINI_API_KEY="YOUR_GEMINI_KEY_HERE"
   PEXELS_API_KEY="YOUR_PEXELS_KEY_HERE"
   ELEVENLABS_API_KEY="YOUR_ELEVENLABS_KEY_HERE"
   SHOTSTACK_API_KEY="YOUR_SHOTSTACK_KEY_HERE"
   ```

---

## ▶️ How to Run

Once the setup is complete, you can run the entire pipeline with a single command from the project's root directory:

### FastAPI Server Mode (Recommended)

```bash
export PYTHONPATH="backend"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Trigger a pipeline run:

```bash
curl -s -X POST 'http://127.0.0.1:8000/pipeline' -H 'Content-Type: application/json' -d '{"niche":"stoicism","upload":false}' | jq .
```

### Local Renderer (Free Alternative)

Set environment variable before starting the server:

```bash
export RENDER_BACKEND=local
export FAST_MODE=1   # optional, limits scenes & durations
```

Pipeline response will include `final_video_url` pointing to a local path like `temp/render_local/final_video.mp4`. Serve the file via:

```bash
curl -O 'http://127.0.0.1:8000/files/final_video.mp4'
```

Requirements for local renderer:
- `ffmpeg` installed (`brew install ffmpeg` on macOS)
- Narration audio files produced by ElevenLabs (or placeholders) present under `temp/`

### Choosing a Backend
| Backend | Env Setting | Pros | Cons |
|---------|-------------|------|------|
| Shotstack | `RENDER_BACKEND=shotstack` (default) | Cloud-grade editing, captions, scalable | Requires API key & credits |
| Local FFmpeg | `RENDER_BACKEND=local` | Free, offline, no external render API | Basic merge only (no animated captions yet) |

If quality isn’t critical or you’re just iterating logic, start with the local backend.

### Self-Hosting Stable Video Diffusion (Experimental)

You can self-host an open Stable Video Diffusion model to avoid paid generative APIs:

#### Option 1: Docker (preferred if image available)
```
docker run --gpus all -p 7860:7860 your-svd-image:latest
```

#### Option 2: Conda Environment
```
conda create -n svd python=3.10 -y
conda activate svd
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install diffusers transformers accelerate safetensors fastapi uvicorn
python server.py  # Your wrapper exposing /generate and /status endpoints
```

Set required environment variables before starting the AutoVidAI backend:
```
export MEDIA_SOURCE=svd
export STABLE_VIDEO_SERVER_URL=http://127.0.0.1:7860
```

Keep the machine running while jobs are active. If the server goes down mid-generation, the pipeline will fall back gracefully to a placeholder clip.

---

## � Deployment (Frontend + Backend)

Quick cloud deploy (no VM): use the Render blueprint included in this repo. See DEPLOY.md for step‑by‑step instructions to deploy both backend and frontend on Render in minutes. Optional instructions for using Vercel for the frontend are included there as well.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/mamun-apu/automatic-video-generating-ai-engine)

This repo includes a Docker-based production setup that serves the frontend as static files via Nginx and proxies API/file requests to the FastAPI backend.

### Prerequisites
- Docker and Docker Compose installed
- An `.env` file at the project root (copy from `.env.example`)

### 1) Configure environment
Copy the example file and fill in keys. For a quick start without external costs, set `RENDER_BACKEND=local`.

```bash
cp .env.example .env
# Edit .env and provide keys or set RENDER_BACKEND=local
```

Note: When using Docker/Nginx, leave `VITE_API_BASE` empty so the frontend calls the backend via same-origin `/api` and `/files` paths.

### 2) Build and run with Docker Compose

```bash
docker compose up -d --build
```

This starts two services:
- backend (FastAPI + Uvicorn) on an internal network at port 8000
- web (Nginx serving the built Vite app) exposed at http://localhost:8080

Routes:
- Frontend UI: http://localhost:8080
- API health: http://localhost:8080/api/health
- Dependency health: http://localhost:8080/api/health/deps
- Local files: http://localhost:8080/files/your_video.mp4

Rendered files are persisted in a Docker volume named `render_data` and mounted at `backend:/app/temp/render_local`.

### 3) Logs and troubleshooting

```bash
docker compose logs -f backend
docker compose logs -f web
```

If the web container returns 502s, ensure the backend is healthy (Compose waits on `/health`).

### 4) Cloud deployment options

- Single VM (recommended to start): copy the repo, create `.env`, and run `docker compose up -d --build`. Put your VM behind a domain and TLS (e.g., Caddy, Nginx, Traefik).
- Split hosting: build and deploy the frontend to a static host (Vercel/Netlify) and deploy the backend to a server (Render/Fly.io). In that case set `VITE_API_BASE` in the frontend environment to your backend URL and rebuild.

### 5) Stopping and cleanup

```bash
docker compose down
# Remove persisted rendered videos (optional)
docker volume rm automatic-video-generating-ai-engine_render_data
```

---

## �🗺️ Future Roadmap

This project is an ongoing proof-of-concept. The planned next steps include:

- **Stage 5 (Distributor):** Implementing programmatic uploads using the YouTube Content API, handling OAuth 2.0 for user authentication.
- **Caption Overlay for Local Backend:** Add burned-in subtitles via ffmpeg `drawtext` or SRT workflows.
- **Scheduling & Job Queues:** Integrating APScheduler for autonomous, scheduled runs and eventually moving to a more robust job queue system like Celery/Redis.
- **Front-End Control Panel:** Building a React-based UI to manage niches, view render history, and provide a real-time logging dashboard (likely via WebSockets).
- **CI/CD:** Setting up a simple CI/CD pipeline with GitHub Actions for automated testing and deployment.

---

## 🤝 Contributing

Feel free to open issues or pull requests with suggestions!

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

