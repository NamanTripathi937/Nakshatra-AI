import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import connect_to_mongo, close_mongo_connection
from app.api.routes import auth, billing, sessions, chat

# ----- Logging -----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nakshatra-backend")

# ----- Database Lifespan -----
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

# ----- App -----
app = FastAPI(title="Nakshatra AI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nakshatra-ai.tech",        # primary production frontend
        "https://www.nakshatra-ai.tech",    # secondary production frontend
        "https://nakshatra-ai.vercel.app",  # legacy Vercel frontend
        "http://localhost:3000",            # local development
    ],
    allow_credentials=True,                 
    allow_methods=["*"],                    
    allow_headers=["*"],                    
)

# Include Routers
app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(sessions.router)
app.include_router(chat.router)


@app.get("/ping")
def ping():
    """Used by frontend to cold-start backend."""
    logger.info("Ping received")
    return {"status": "ok"}
