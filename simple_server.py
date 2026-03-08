from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    with open("ui/index.html", "r", encoding="utf-8") as f:
        return StreamingResponse(iter([f.read()]), media_type="text/html")

@app.get("/health")
def health():
    return {"status": "healthy", "version": "2.1.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
