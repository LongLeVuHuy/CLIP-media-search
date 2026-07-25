from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from search_media import search_media


BASE_DIR = Path(__file__).resolve().parent
MEDIA_FOLDER = (BASE_DIR / "input_media").resolve()

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/api/search")
def api_search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(12, ge=1, le=30),
):
    try:
        raw_results = search_media(q, top_k)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    results = []

    for item in raw_results:
        file_path = Path(
            str(item.get("file_path", ""))
        ).resolve()

        try:
            relative_path = file_path.relative_to(MEDIA_FOLDER)
        except ValueError:
            continue

        results.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "media_type": item.get("media_type"),
            "score": item.get("score"),
            "best_timestamp_seconds": item.get(
                "best_timestamp_seconds"
            ),
            "media_url": (
                "/media/"
                + quote(relative_path.as_posix())
            ),
        })

    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@app.get("/media/{file_path:path}")
def serve_media(file_path: str):
    requested_file = (
        MEDIA_FOLDER / file_path
    ).resolve()

    try:
        requested_file.relative_to(MEDIA_FOLDER)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Đường dẫn không hợp lệ.",
        )

    if not requested_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy file.",
        )

    return FileResponse(requested_file)