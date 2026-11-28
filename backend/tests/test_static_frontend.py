from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import mount_frontend_assets


def test_frontend_assets_are_served_after_existing_api_routes(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "<!doctype html><html><body><div id='root'>RadOnc</div></body></html>",
        encoding="utf-8",
    )
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("window.radonc = true;", encoding="utf-8")

    application = FastAPI()

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    assert mount_frontend_assets(application, tmp_path) is True

    client = TestClient(application)
    page = client.get("/")
    asset = client.get("/assets/app.js")
    api = client.get("/health")

    assert page.status_code == 200
    assert "id='root'" in page.text
    assert asset.status_code == 200
    assert asset.text == "window.radonc = true;"
    assert api.status_code == 200
    assert api.json() == {"status": "ok"}


def test_frontend_assets_are_not_mounted_without_a_production_index(tmp_path: Path) -> None:
    application = FastAPI()
    assert mount_frontend_assets(application, tmp_path) is False
    assert TestClient(application).get("/").status_code == 404
