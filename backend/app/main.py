from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.scada import router as scada_router

app = FastAPI(title="NL2Chart API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scada_router)

@app.get("/")
async def root():
    return {"message": "NL2Chart API is running", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
