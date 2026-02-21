import asyncio
from playwright.async_api import async_playwright


async def function(url: str):
    async with async_playwright() as p:
        print("Launching browser...")

        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"Navigating to {url}...")
        await page.goto(url, timeout=10000)

        print(f"Page loaded: {url}")
        await page.wait_for_timeout(2000)

        print(f"Extracting content from {url}...")
        content = await page.content()

        await browser.close()
        return content


if __name__ == "__main__":
    url = "https://www.example.com"
    content = asyncio.run(function(url))
    print(content)
