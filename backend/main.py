from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import socket
import uvicorn

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    model: str
    messages: list
    temperature: float = 0.7
    max_tokens: int = 1024

def check_port(host: str, port: int, timeout: float = 3.0) -> bool:
    """Check if a port is open and accepting connections"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except socket.error:
        return False

@app.post("/api/chat")
async def chat_completion(request: ChatRequest):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": request.model,
        "messages": request.messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    
    try:
        # Verify Ollama is running first
        if not check_port("localhost", 11434):
            raise HTTPException(
                status_code=503,
                detail="Ollama service not available on port 11434. Please ensure Ollama is running."
            )
        
        response = requests.post(
            "http://localhost:11434/v1/chat/completions",
            verify=False,
            json=payload,
            headers=headers,
            timeout=600
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request to Ollama timed out")
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with Ollama: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/models")
async def get_available_models():
    return {
        "models": [
            {"id": "llama3.2-vision:11b", "name": "Llama3.2 Vision (11B)"},
            {"id": "qwen2.5-coder:0.5b", "name": "Qwen2.5 Coder (0.5B)"}
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting FastAPI server. Verify these endpoints:")
    print("• Ollama: http://localhost:11434")
    print("• FastAPI: http://localhost:8000/api/models")
    print("• Health check: http://localhost:8000/health")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")