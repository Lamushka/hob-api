from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
import time, hmac, hashlib, os

API_KEY = os.getenv("API_KEY", "dev_key_123")
HMAC_SECRET = os.getenv("HMAC_SECRET", "").encode()

app = FastAPI(title="Human-or-Bot Classifier API", version="1.0.0")

class ContextItem(BaseModel):
    sender: str
    text: str
    timestamp: str | None = None

class PredictIn(BaseModel):
    message_id: str
    dialog_id: str | None = None
    text: str = Field(min_length=1)
    lang: str | None = "ru"
    timestamp: str | None = None
    context: list[ContextItem] | None = None
    meta: dict | None = None

class PredictOut(BaseModel):
    message_id: str
    prob_bot: float
    label: str
    model_version: str
    inference_ms: int
    request_id: str | None = None
    calibration: dict | None = None

def verify_api_key(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.split()[1]
    if token != API_KEY:
        raise HTTPException(403, "Invalid token")

def verify_hmac(sig: str | None, raw_body: bytes):
    if not HMAC_SECRET:  # optional
        return
    if not sig:
        raise HTTPException(401, "Missing signature")
    expected = hmac.new(HMAC_SECRET, raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(403, "Bad signature")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    # In real life: check model file loaded, DB connections, etc.
    return {"ready": True, "model_loaded": True}

@app.get("/version")
def version():
    return {"build": "local", "model_version": "hob-bert-mini-2025-09-01"}

@app.post("/v1/predict", response_model=PredictOut)
async def predict(
    req: Request,
    payload: PredictIn,
    authorization: str | None = Header(default=None),
    x_hob_signature: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
):
    raw = await req.body()
    verify_api_key(authorization)
    verify_hmac(x_hob_signature, raw)

    t0 = time.time()

    # TODO: Replace with real preprocessing + model inference
    # Example heuristic: longer messages => slightly less likely bot
    base = 0.7
    adjust = -min(len(payload.text), 200) / 1000.0
    prob_bot = max(0.0, min(1.0, base + adjust))

    label = "bot" if prob_bot >= 0.5 else "human"
    inference_ms = int((time.time() - t0) * 1000)

    return PredictOut(
        message_id=payload.message_id,
        prob_bot=prob_bot,
        label=label,
        model_version="hob-bert-mini-2025-09-01",
        inference_ms=inference_ms,
        request_id=x_request_id,
        calibration={"method": "none"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
@app.get("/")
def root():
    return {"service": "hob-api", "status": "ok"}
