import asyncio
import sys

from fastapi import FastAPI, HTTPException
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from pydantic import HttpUrl


if sys.platform == "win32" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


app = FastAPI()


def _fetch_page_content(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=10000)
            page.wait_for_timeout(2000)
            return page.content()
        finally:
            browser.close()


@app.get("/")
async def root(url: HttpUrl):
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
