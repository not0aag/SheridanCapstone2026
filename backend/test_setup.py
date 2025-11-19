from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "SafeDrive AI Backend - Setup Successful!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "safedrive-backend"}
