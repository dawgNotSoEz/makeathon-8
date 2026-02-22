import asyncio
import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from backend.core.config import config


router = APIRouter()


def _read_gazettes_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _candidate_paths() -> list[Path]:
    cwd = Path.cwd()
    project_root = Path(__file__).resolve().parents[2]
    data_file = "Gazetted_data_18-02-2026.json"
    env_path = Path(config.policies_path) / data_file

    return [
        env_path,
        Path(config.policies_path) / data_file,
        Path("backend/data/policies") / data_file,
        project_root / "backend" / "data" / "policies" / data_file,
        cwd / "backend" / "data" / "policies" / data_file,
        cwd / data_file,
    ]


def _find_existing_file() -> Path | None:
    for path in _candidate_paths():
        if path.exists() and path.is_file():
            return path
    return None


@router.get("/gazettes")
async def get_gazettes():
    path = _find_existing_file()
    if path is None:
        return JSONResponse({"error": "Failed to fetch gazette data"}, status_code=404)

    try:
        return await asyncio.to_thread(_read_gazettes_json, path)
    except Exception:
        try:
            return FileResponse(path, media_type="application/json")
        except Exception:
            return JSONResponse({"error": "Failed to fetch gazette data"}, status_code=500)
