
import pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 1.0
import pyperclip
import platform
import pyscreeze
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path


CITY = "Chennai"
URL = f"https://wttr.in/{CITY}?format=%l:+%C,+%t"

OUTPUT_DIR = Path(__file__).resolve().parent
SYSTEM = platform.system()     
MOD = "command" if SYSTEM == "Darwin" else "ctrl"

pyautogui.FAILSAFE = True           
pyautogui.PAUSE = 0.4               


def launch_app(name: str) -> None:
    """Launch an application by logical name: 'chrome' or 'excel'."""
    if SYSTEM == "Windows":
        cmd = {"chrome": "chrome", "excel": "excel"}[name]
        subprocess.Popen(["cmd", "/c", "start", "", cmd], shell=False)
    elif SYSTEM == "Darwin":
        app = {"chrome": "Google Chrome", "excel": "Microsoft Excel"}[name]
        subprocess.Popen(["open", "-a", app])
    else:
        cmd = {"chrome": "google-chrome", "excel": "libreoffice --calc"}[name]
        subprocess.Popen(cmd.split())


def paste_text(text: str) -> None:
    """Paste text via clipboard (safe for symbols like the degree sign)."""
    pyperclip.copy(text)
    time.sleep(0.2)
    pyautogui.hotkey(MOD, "v")
    time.sleep(0.3)


def fetch_weather(max_attempts: int = 5) -> str:
    """Open Chrome, load the page and copy its text. Retries if slow."""
    print("[1/6] Opening Chrome...")
    launch_app("chrome")
    time.sleep(4)                                   # wait for Chrome window

    pyautogui.hotkey(MOD, "t")                      # fresh tab -> focused window
    time.sleep(1)
    pyautogui.hotkey(MOD, "l")                      # focus address bar
    paste_text(URL)
    pyautogui.press("enter")

    print("[2/6] Waiting for page and copying data...")
    sentinel = "__WAITING__"
    for attempt in range(1, max_attempts + 1):
        time.sleep(3 + attempt)                     # wait longer each retry
        pyperclip.copy(sentinel)
        pyautogui.click(pyautogui.size().width // 2,
                        pyautogui.size().height // 2)  # focus page body
        pyautogui.hotkey(MOD, "a")
        pyautogui.hotkey(MOD, "c")
        time.sleep(0.5)
        text = pyperclip.paste().strip()
        if text and text != sentinel and CITY.lower() in text.lower():
            print(f"      Fetched: {text}")
            return text
        print(f"      Page not ready (attempt {attempt}/{max_attempts})...")
    raise RuntimeError("Could not copy weather data from the page.")


def make_comment(weather: str) -> str:
    """Generate a short comment based on the temperature in the data."""
    match = re.search(r"([+-]?\d+)\s*°?C", weather)
    if not match:
        return "Check conditions before heading out"
    temp = int(match.group(1))
    if temp >= 36:
        return "Very hot - avoid midday outdoor activities"
    if temp >= 30:
        return "Warm - good for outdoor activities in the morning/evening"
    if temp >= 20:
        return "Pleasant - good for outdoor activities"
    return "Cool - carry a light jacket"


def fill_excel(timestamp: str, weather: str, comment: str) -> None:
    """Open Excel, create a blank workbook and type the report rows."""
    print("[3/6] Opening Excel...")
    launch_app("excel")
    time.sleep(8)                                   # Excel is slow to start

    pyautogui.hotkey(MOD, "n")                      # new blank workbook
    time.sleep(3)

    print("[4/6] Writing the row...")
    # Header row
    for i, header in enumerate(["Date & Time", "Weather Data", "Comment"]):
        pyautogui.typewrite(header, interval=0.03)
        pyautogui.press("tab" if i < 2 else "enter")
    # Excel returns to column A after Tab...Tab...Enter, so we are on row 2 now.

    # Data row (clipboard paste keeps special characters intact)
    for i, value in enumerate([timestamp, weather, comment]):
        paste_text(value)
        pyautogui.press("tab" if i < 2 else "enter")

    # Widen columns so the screenshot is readable: select all + autofit
    if SYSTEM == "Windows":
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("alt")
        for key in ["h", "o", "i"]:                 # Home > Format > AutoFit Col
            pyautogui.press(key)
        pyautogui.hotkey("ctrl", "home")
    else:
        pyautogui.hotkey("command", "a")
        pyautogui.hotkey("command", "up")           # back to top-left area
    time.sleep(1)


def save_workbook(xlsx_path: Path) -> None:
    """Save via the Save As dialog using the full path."""
    print(f"[5/6] Saving {xlsx_path.name} ...")
    if SYSTEM == "Windows":
        pyautogui.press("f12")                      # classic Save As dialog
    else:
        pyautogui.hotkey(MOD, "s")
    time.sleep(3)

    paste_text(str(xlsx_path))
    pyautogui.press("enter")
    time.sleep(3)


def take_screenshot(png_path: Path) -> None:
    print(f"[6/6] Taking screenshot -> {png_path.name}")
    time.sleep(1)
    pyautogui.screenshot(str(png_path))


def main() -> None:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")   # generated at run time

    xlsx_path = OUTPUT_DIR / f"daily_report_{date_str}.xlsx"
    png_path = OUTPUT_DIR / f"daily_report_{date_str}_screenshot.png"

    # Remove an older file from a previous run so no overwrite prompt appears
    if xlsx_path.exists():
        xlsx_path.unlink()

    print("Starting in 5 seconds - do not touch mouse/keyboard...")
    time.sleep(5)

    weather = fetch_weather()
    comment = make_comment(weather)
    fill_excel(timestamp, weather, comment)
    save_workbook(xlsx_path)
    take_screenshot(png_path)

    print("\nDone!")
    print(f"  Excel file : {xlsx_path}")
    print(f"  Screenshot : {png_path}")


if __name__ == "__main__":
    main()
