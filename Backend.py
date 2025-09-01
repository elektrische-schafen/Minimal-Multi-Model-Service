from fastapi import FastAPI
from fastapi.responses import StreamingResponse, Response , JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from dotenv import load_dotenv
from Agent import orchestrator
from uuid import uuid1
import time
import json
import os

load_dotenv()

class ChatRequest(BaseModel):
    query : str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/v1/items/analyze")
async def analyze_item(request: ChatRequest):
    print("Received request:", request)
    
    query = request.query
    session_id = uuid1()

    response = orchestrator(query,session_id)

   
    return JSONResponse(response)

@app.get("/v1/status")
async def get_status():
    return {
        "status": "ok",
        "message": "API is running smoothly",
        "version": "1.0.0"
    }

        

