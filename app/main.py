from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routes import events, transactions, users
import logging

Base.metadata.create_all(bind=engine)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(transactions.router)
app.include_router(users.router)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.get("/")
def root():
    logger.info("Root endpoint called")
    return Response("API is running", media_type="text/plain")
