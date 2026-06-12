import os
import backend.model as model
from backend.data import engine
from backend.routers import auth_router, interview_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Create tables (wrapped so a DB error doesn't kill startup)
try:
    model.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[WARN] DB table creation failed: {e}")

app = FastAPI(title="InterviewAI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(interview_router)

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "InterviewAI API running"}

# Mount frontend LAST — only if the folder exists
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")