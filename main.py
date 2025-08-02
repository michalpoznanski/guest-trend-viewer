from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Guest Trend Viewer is working!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Railway ustawia PORT jako zmienną środowiskową
    uvicorn.run(app, host="0.0.0.0", port=port) 