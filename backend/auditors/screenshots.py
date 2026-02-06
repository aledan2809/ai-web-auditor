"""
Screenshot Module - Captures website screenshots
"""

import asyncio
import base64
from pathlib import Path
from typing import Dict, Optional
import os


async def take_screenshots(url: str, mobile: bool = True) -> Dict[str, Optional[str]]:
    """Take desktop and mobile screenshots of a URL"""
    screenshots = {
        'desktop': None,
        'mobile': None
    }

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # Desktop screenshot
            desktop_context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            desktop_page = await desktop_context.new_page()
            await desktop_page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1)  # Wait for animations

            desktop_bytes = await desktop_page.screenshot(full_page=False)
            screenshots['desktop'] = base64.b64encode(desktop_bytes).decode('utf-8')

            await desktop_context.close()

            # Mobile screenshot
            if mobile:
                mobile_context = await browser.new_context(
                    viewport={'width': 375, 'height': 812},
                    user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
                )
                mobile_page = await mobile_context.new_page()
                await mobile_page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(1)

                mobile_bytes = await mobile_page.screenshot(full_page=False)
                screenshots['mobile'] = base64.b64encode(mobile_bytes).decode('utf-8')

                await mobile_context.close()

            await browser.close()

    except ImportError:
        print("Playwright not available for screenshots")
    except Exception as e:
        print(f"Screenshot error: {e}")

    return screenshots


async def save_screenshot(base64_data: str, filename: str) -> str:
    """Save a base64 screenshot to file"""
    output_dir = Path(__file__).parent.parent / 'data' / 'screenshots'
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / filename

    image_data = base64.b64decode(base64_data)
    with open(file_path, 'wb') as f:
        f.write(image_data)

    return str(file_path)
