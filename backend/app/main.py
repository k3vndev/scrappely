import asyncio
import os
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from pydantic import HttpUrl


if sys.platform == "win32" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


app = FastAPI()


def _get_playwright_executable_path() -> Optional[str]:
    executable_path = os.getenv("PLAYWRIGHT_EXECUTABLE_PATH")
    if executable_path is None:
        return None

    normalized_path = executable_path.strip()
    return normalized_path or None


def _fetch_page_content(url: str) -> str:
    with sync_playwright() as p:
        executable_path = _get_playwright_executable_path()
        launch_kwargs = {"headless": True}
        if executable_path is not None:
            launch_kwargs["executable_path"] = executable_path

        browser = p.chromium.launch(**launch_kwargs)
        try:
            page = browser.new_page()
            page.goto(url, timeout=10000)
            page.wait_for_timeout(2000)
            return page.content()
        finally:
            browser.close()


@app.get("/")
async def root(url: Optional[HttpUrl] = None):
    if url is None:
        return {"message": "Hello! Please provide a URL as a query parameter."}

    try:
        content = await asyncio.to_thread(_fetch_page_content, str(url))

        return {
            "message": f"Hello, FastAPI! You provided the URL: {url}",
            "content": content,
        }
    except PlaywrightTimeoutError as exc:
        raise HTTPException(
            status_code=504, detail=f"Timed out loading URL: {url}"
        ) from exc
    except PlaywrightError as exc:
        raise HTTPException(
            status_code=502, detail=f"Browser automation failed: {exc}"
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc
