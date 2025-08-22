import os
import time
import logging
from fastapi import FastAPI, Response, Request, status
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from prometheus_fastapi_instrumentator import Instrumentator
from starlette.responses import JSONResponse, FileResponse

from pathlib import Path
from logging.handlers import RotatingFileHandler
import re
import sqlite3

from oembed_to_title import get_title
from url_conversion import build_spotify_url
from data_transfer_objects import SpotifyType, SpotifyCodeDTO
from oembed_to_album_image import save_album_data
from url_to_code_image import save_spotify_code_data
from album_image_to_colors import get_colors_from_image
from code_image_to_bars import get_encoded_bars_from_image
from url_to_oembed import get_oembed_data

load_dotenv()

IS_PRODUCTION = os.getenv("IS_PRODUCTION", "False").lower() in ("true", "1", "yes")
EXTERNAL_ORIGIN = os.getenv("EXTERNAL_ORIGIN", "")

JOB_DIR = Path(__file__).parent / "jobs"
JOB_DIR = JOB_DIR.resolve()
DB_DIR = Path(__file__).parent / "db"
DB_DIR = DB_DIR.resolve()

SPOTIFY_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{22}$')
SPOTIFY_TYPE_PATTERN = re.compile(r'^(track|album|episode|playlist)$')
SPOTIFY_JOB_ID_PATTERN = re.compile(r'^(track|album|episode|playlist)-[a-zA-Z0-9]{22}$')

logger = logging.getLogger("spotify_code_api")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    "logs/spotify_api.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler.setFormatter(formatter)
logger.addHandler(handler)

app_kwargs = {
    "title": "Spotify Code API",
    "version": "1.0.2",
}

if IS_PRODUCTION:
    app_kwargs["docs_url"] = None
    app_kwargs["redoc_url"] = None
    app_kwargs["openapi_url"] = None

app = FastAPI(**app_kwargs)

origins = [
    "http://localhost:5173",
    EXTERNAL_ORIGIN,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute", "3/second"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(
    status_code=429, content={"detail": "Too many requests, please try again later."}))

if not IS_PRODUCTION:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status {response.status_code} for {request.method} {request.url}")
    return response

@app.get("/spotify/health")
@limiter.limit("30/minute")
def server_health_check(request: Request):
    return {"status": "ok", "message": "Spotify Code API is running"}

@app.get("/spotify/health/oembed")
def oembed_health_check(request: Request):
    try:
        get_oembed_data("https://open.spotify.com/track/0c6xIDDpzE81m2q797ordA", debug=False)
        return {"status": "ok", "message": "oEmbed service is reachable"}
    except Exception as e:
        logger.error(f"oEmbed health check failed: {e}", exc_info=True)
        return JSONResponse(status_code=503, content={"detail": "oEmbed service is not reachable"})

@app.get("/spotify/code/{spotify_type}/{spotify_id}")
@limiter.limit("10/minute")
def get_spotify_code(spotify_id: str, spotify_type: SpotifyType, request: Request, response: Response):
    result = process_request(spotify_id, spotify_type, response=response)
    return result

@app.get("/spotify/album/{job_id}/image")
@limiter.limit("10/minute")
def get_album_image(job_id: str, request: Request, response: Response):
    try:
        sanitize_check_job_id(job_id)
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

    job_dir = JOB_DIR / job_id
    image_path = job_dir / "album_img.jpeg"

    if not image_path.exists():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": "Album image not found"}

    return FileResponse(
        image_path,
        media_type="image/jpeg",
        # filename=f"album_img_{job_id}.png",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/spotify/pdf/{job_id}/a4")
@limiter.limit("10/minute")
def get_a4_pdf(job_id: str, request: Request, response: Response):
    try:
        sanitize_check_job_id(job_id)
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

    job_dir = JOB_DIR / job_id
    pdf_path = job_dir / "a4.pdf"

    if not pdf_path.exists():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": "A4 PDF not found"}

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        # filename=f"a4_{job_id}.pdf",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/spotify/pdf/{job_id}/minimal")
@limiter.limit("10/minute")
def get_minimal_pdf(job_id: str, request: Request, response: Response):
    try:
        sanitize_check_job_id(job_id)
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

    job_dir = JOB_DIR / job_id
    pdf_path = job_dir / "minimal.pdf"

    if not pdf_path.exists():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": "Minimal PDF not found"}

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        # filename=f"minimal_{job_id}.pdf",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    logger.error(f"Unhandled exception for {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


def process_request(spotify_id: str, spotify_type: SpotifyType, response: Response, debug: bool=False): #-> SpotifyCodeDTO |dict[str, str]:
    job_id = f"{spotify_type.value}-{spotify_id}"
    try:
        sanitize_check_job_id(job_id)
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

    job_dir = JOB_DIR / job_id
    debug_dir = Path(job_dir) / "debug_outputs"
    debug_dir.mkdir(parents=True, exist_ok=True)

    now = time.time()
    os.utime(job_dir, (now, now))

    log_to_db(spotify_id, spotify_type)

    spotify_url = build_spotify_url(spotify_type, spotify_id)

    code_img_path = job_dir / "code_img.png"
    album_img_path = job_dir / "album_img.jpeg"
    pdf_a4_path = job_dir / "a4.pdf"
    pdf_minimal_path = job_dir / "minimal.pdf"

    regenerate_files = not (code_img_path.exists() and album_img_path.exists()
                            and pdf_a4_path.exists() and pdf_minimal_path.exists())

    oembed_data = None
    title = None
    colors_dto = None

    try:
        oembed_data = get_oembed_data(spotify_url, debug=debug)
    except Exception as e:
        logger.error(f"Error fetching oEmbed data for {spotify_id}/{spotify_type}: {e}", exc_info=True)

    try:
        if regenerate_files:
            save_spotify_code_data(spotify_url, str(code_img_path), debug=debug)
    except Exception as e:
        logger.error(f"Error fetching Spotify code data for {spotify_id}/{spotify_type}: {e}", exc_info=True)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"detail": f"An error occurred while fetching Spotify code data: {str(e)}"}

    try:
        if regenerate_files and oembed_data:
            save_album_data(oembed_data, image_path=str(album_img_path), pdf_a4_path=str(pdf_a4_path),
                            pdf_minimal_path=str(pdf_minimal_path), debug=debug)

        if oembed_data:
            title = get_title(oembed_data, debug=debug)
    except Exception as e:
        logger.warning(f"Error saving album data for {spotify_id}/{spotify_type}: {e}", exc_info=True)

    try:
        bars_dto = get_encoded_bars_from_image(str(code_img_path), debug=debug, debug_dir=str(debug_dir))
    except Exception as e:
        logger.error(f"Error processing request for {spotify_id}/{spotify_type}: {e}", exc_info=True)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"detail": f"An error occurred while processing the request: {str(e)}"}

    try:
        colors_dto = get_colors_from_image(str(album_img_path), debug=debug)
    except Exception as e:
        logger.warning(f"Error extracting colors from album image for {spotify_id}/{spotify_type}: {e}", exc_info=True)

    spotify_code_dto = SpotifyCodeDTO(
        job_id=job_id,
        spotify_url=spotify_url,
        spotify_id=spotify_id,
        type=spotify_type.value,
        title=title,
        bars=bars_dto,
        album_image_color=colors_dto
    )
    return spotify_code_dto

def sanitize_check_job_id(job_id: str) -> None:
    parts = job_id.split("-")
    if (len(parts) != 2 or not SPOTIFY_TYPE_PATTERN.fullmatch(parts[0])
            or not SPOTIFY_ID_PATTERN.fullmatch(parts[1])):
        raise ValueError("Invalid job ID format")

    job_dir = (JOB_DIR / job_id).resolve()

    if not str(job_dir).startswith(str(JOB_DIR)):
        raise ValueError("Invalid job ID format or directory traversal attempt")

def log_to_db(spotify_id: str, spotify_type: SpotifyType) -> None:
    db_path = DB_DIR / "requests.db"
    DB_DIR.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_str DATETIME DEFAULT CURRENT_TIMESTAMP,
                timestamp_unix FLOAT,
                spot_id TEXT,
                spot_type TEXT
            )"""
        )
        c.execute("INSERT INTO requests (timestamp_unix, spot_id, spot_type) VALUES (?, ?, ?)",
                  (time.time(), spotify_id, spotify_type.value))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error inserting request {spotify_id}/{spotify_type}: {e}", exc_info=True)
