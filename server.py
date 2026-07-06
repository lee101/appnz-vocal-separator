import base64
import os
import tempfile
import threading
import urllib.request

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

PORT = int(os.environ.get("PORT", "5000"))
state = {"loaded": False, "error": ""}
MODEL = None
LOCK = threading.Lock()

COG_SCHEMA = {
    "outputKind": "json",
    "inputs": [
        {
            "name": "audio",
            "type": "audio",
            "description": "Audio file (https URL or data URI)",
            "required": True,
            "order": 0,
        },
        {
            "name": "stems",
            "type": "string",
            "description": "two = vocals+instrumental, four = vocals/drums/bass/other",
            "default": "two",
            "choices": ["two", "four"],
            "required": False,
            "order": 1,
        },
    ],
}


def _load():
    global MODEL
    try:
        import torch
        from demucs.pretrained import get_model

        m = get_model("htdemucs")
        m.eval()
        if torch.cuda.is_available():
            m.cuda()
        MODEL = m
        state["loaded"] = True
    except Exception as e:
        state["error"] = str(e)


def fetch_bytes(v):
    if not isinstance(v, str) or not v:
        raise HTTPException(status_code=400, detail="missing audio")
    if v.startswith("data:"):
        return base64.b64decode(v.partition(",")[2])
    if v.startswith(("http://", "https://")):
        with urllib.request.urlopen(v, timeout=120) as r:
            return r.read()
    return base64.b64decode(v)


def separate(data, stems):
    import torch
    from demucs.apply import apply_model
    from demucs.audio import AudioFile, save_audio

    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "input")
        with open(src, "wb") as f:
            f.write(data)
        wav = AudioFile(src).read(
            streams=0, samplerate=MODEL.samplerate, channels=MODEL.audio_channels
        )
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / (ref.std() + 1e-8)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        with torch.no_grad():
            sources = apply_model(MODEL, wav[None], device=device, progress=False)[0]
        sources = sources * ref.std() + ref.mean()
        names = list(MODEL.sources)
        if stems == "four":
            parts = dict(zip(names, sources))
        else:
            vocals = sources[names.index("vocals")]
            parts = {"vocals": vocals, "instrumental": sources.sum(0) - vocals}
        out = {}
        for name, tensor in parts.items():
            path = os.path.join(td, f"{name}.mp3")
            save_audio(tensor.cpu(), path, MODEL.samplerate)
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            out[name] = f"data:audio/mpeg;base64,{b64}"
        return out


app = FastAPI(title="appnz-vocal-separator", openapi_url=None)


@app.on_event("startup")
def startup():
    threading.Thread(target=_load, daemon=True).start()


@app.get("/health-check")
def health_check():
    if state["error"]:
        return {"status": "SETUP", "error": state["error"]}
    return {"status": "READY" if state["loaded"] else "SETUP"}


@app.get("/healthz")
def healthz():
    if not state["loaded"]:
        return JSONResponse({"status": "loading", "error": state["error"]}, status_code=503)
    return {"status": "ok"}


@app.get("/openapi.json")
def openapi_json():
    return COG_SCHEMA


@app.post("/predictions")
def predictions(payload: dict):
    if not state["loaded"]:
        return JSONResponse(
            {"status": "failed", "error": state["error"] or "model loading"},
            status_code=503,
        )
    body = payload.get("input") or {}
    stems = body.get("stems") or "two"
    if stems not in ("two", "four"):
        return JSONResponse(
            {"status": "failed", "error": "stems must be two or four"}, status_code=400
        )
    try:
        data = fetch_bytes(body.get("audio"))
        with LOCK:
            out = separate(data, stems)
        return {"status": "succeeded", "output": out}
    except HTTPException as e:
        return JSONResponse({"status": "failed", "error": e.detail}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse({"status": "failed", "error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
