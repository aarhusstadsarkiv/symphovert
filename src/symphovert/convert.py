from pathlib import Path
from subprocess import CalledProcessError
from subprocess import run as run_process
from time import sleep

import pyautogui
import pyperclip

from .exceptions import SymphonyError

pyautogui.PAUSE = 1
pyautogui.FAILSAFE = False


def copypaste(str_to_copy: str) -> None:
    pyperclip.copy(f"{str_to_copy}")
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")


def save_as(file: str) -> None:
    pyautogui.hotkey("ctrl", "shift", "s", interval=0.1)
    copypaste(file)


def symphony_convert(src: Path, dst: Path) -> None:
    # If outfile exists, delete it first.
    if dst.is_file():
        dst.unlink()

    # Open IBM Symphony and do unholy things with pyautogui
    try:
        run_process("symphony.exe", shell=True, check=True, capture_output=True)
    except CalledProcessError as error:
        error_msg = error.stderr.strip().decode()
        raise SymphonyError(f"Execution of IBM Symphony failed with error: {error_msg}")
    else:
        # Wait a bit, then open the file
        sleep(2)
        pyautogui.hotkey("ctrl", "o", interval=0.5)
        sleep(1)
        copypaste(str(src))
        sleep(0.5)

        # Symphony opens an extra menu when ctrl+o is used for... reasons.
        # Esc closes it.
        pyautogui.press("escape")
        sleep(2)

        dst.parent.mkdir(parents=True, exist_ok=True)

        # Save the file as ODT.
        save_as(str(dst))
        sleep(2)

        # Kill Symphony
        run_process("taskkill /f /im symphony*", check=False, shell=True, capture_output=True)
        sleep(0.5)
        run_process("taskkill /f /im soffice*", check=False, shell=True, capture_output=True)
        sleep(1)

        # If outfile does not exist after the above, we probably have a
        # problem.
        if not dst.is_file():
            raise SymphonyError(f"Conversion of {src} failed!")
