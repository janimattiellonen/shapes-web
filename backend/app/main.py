from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Shape Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Shape Detection API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


class HelloWorldRequest(BaseModel):
    message: str


class HelloWorldResponse(BaseModel):
    response: str


@app.post("/hello-world", response_model=HelloWorldResponse)
async def hello_world(request: HelloWorldRequest):
    reversed_message = request.message[::-1]
    current_date = datetime.now().strftime("%d.%m.%Y %H.%M.%S")
    response_text = f"{reversed_message} {current_date}"
    return HelloWorldResponse(response=response_text)
