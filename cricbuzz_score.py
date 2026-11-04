import sys

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

URL = "https://www.cricbuzz.com/"

# Live match cards on the homepage are links to a /live-cricket-scores/<id>/...
# page. Replace with the selector you confirmed in DevTools if it differs.
SCORE_SELECTOR = 'a[href*="/live-cricket-scores/"]'

WAIT_TIMEOUT_MS = 15_000          # max time to wait for the element (not a sleep)
SCREENSHOT_PATH = "score.png"


def main() -> int:
    headless = "--headless" in sys.argv

    with sync_playwright() as p:
        # Use the real Google Chrome installed on this machine.
        browser = p.chromium.launch(channel="chrome", headless=headless)
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=30_000)

            # Wait for the score element itself - no fixed sleep.
            try:
                page.wait_for_selector(SCORE_SELECTOR, state="visible",
                                       timeout=WAIT_TIMEOUT_MS)
            except PlaywrightTimeout:
                print("No live match found (score element did not appear "
                      f"within {WAIT_TIMEOUT_MS // 1000}s).")
                page.screenshot(path=SCREENSHOT_PATH)
                print(f"saved {SCREENSHOT_PATH} (page as it looked)")
                return 1

            card = page.locator(SCORE_SELECTOR).first
            card.scroll_into_view_if_needed()

            # Collapse the multi-line card text into readable lines.
            raw = card.inner_text()
            score = "\n".join(line.strip() for line in raw.splitlines()
                              if line.strip())
            print(score)

            page.screenshot(path=SCREENSHOT_PATH)
            print(f"\nsaved {SCREENSHOT_PATH}")
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
