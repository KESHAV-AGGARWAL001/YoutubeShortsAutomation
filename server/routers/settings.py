import os
import json
from fastapi import APIRouter
from server.models.schemas import SettingsData
from server.services.state import PROJECT_ROOT

router = APIRouter()

SETTINGS_FILE = os.path.join(PROJECT_ROOT, "output", "dashboard_settings.json")


def _load_settings() -> SettingsData:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SettingsData(**data)
        except Exception:
            pass
    return SettingsData()


def _save_settings(settings: SettingsData):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.model_dump(), f, indent=2)


@router.get("/settings")
async def get_settings():
    return _load_settings().model_dump()


@router.put("/settings")
async def update_settings(settings: SettingsData):
    _save_settings(settings)
    return {"status": "updated"}
