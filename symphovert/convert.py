"""Tool for converting Lotus SmartSuite files to Open Document format.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import platform
import time
import subprocess
from subprocess import CalledProcessError
from pathlib import Path
import pyperclip
from symphovert.exceptions import SymphonyError

try:
    import pyautogui
except Exception as e:
    raise SymphonyError(f"Failed to import pyautogui with error: {e}")

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------
ACCEPTED_OUT = ["odt", "ods", "odp"]
pyautogui.PAUSE = 0.7
pyautogui.FAILSAFE = False

# -----------------------------------------------------------------------------
# Function Definitions
# -----------------------------------------------------------------------------


def copypaste(str_to_copy: str) -> None:
    pyperclip.copy(f"{str_to_copy}")
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")


def save_as(file: str) -> None:
    pyautogui.hotkey("ctrl", "shift", "s", interval=0.1)
    copypaste(file)


def find_symphony() -> str:

    # Initialise variables
    exe_path: str = ""
    system: str = platform.system()

    # System specific functionality.
    if system == "Windows":
        find_symphony_cmd = r"where.exe *symphony.exe*"
    else:
        raise SymphonyError(
            f"Conversion using IBM Symphony is not supported on {system}."
        )

    # Invoke the command to find Symphony on Windows.
    try:
        cmd = subprocess.run(
            f"{find_symphony_cmd}", shell=True, check=True, capture_output=True
        )
    except CalledProcessError as error:
        # Didn't find executable.
        # Return code != 0
        error_msg = error.stderr.strip().decode()
        raise SymphonyError(
            f"Could not find IBM Symphony with error: {error_msg}"
        )
    else:
        # Remove trailing newline and decode stdout from byte string.
        # Windows needs the quotes. IBM Symphony has more than one exe file
        # after install. Finger's crossed the correct one is always the first
        # Windows finds. :|
        exe_path = f'"{cmd.stdout.strip().decode().splitlines()[0]}"'
        return exe_path


def symphony_convert(
    file: Path, outdir: Path, convert_to: str = "odt"
) -> None:
    # Test if output is accepted
    if convert_to not in ACCEPTED_OUT:
        raise SymphonyError(f"Cannot convert to {convert_to} using Symphony.")
    # Initialise variables
    cmd: str = find_symphony()
    outfile: Path = outdir.joinpath(f"{file.stem}.{convert_to}")

    # If outfile exists, delete it first.
    if outfile.is_file():
        outfile.unlink()

    # Open IBM Symphony and do unholy things with pyautogui
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
    except CalledProcessError as error:
        error_msg = error.stderr.strip().decode()
        raise SymphonyError(
            f"Execution of IBM Symphony failed with error: {error_msg}"
        )
    else:
        # Wait a bit, then open the file
        time.sleep(1.5)
        pyautogui.hotkey("ctrl", "o", interval=0.3)
        time.sleep(0.3)
        copypaste(str(file))

        # Symphony opens an extra menu when ctrl+o is used for... reasons.
        # Esc closes it.
        pyautogui.press("escape")
        time.sleep(2)

        # Save the file as ODT.
        save_as(str(outfile))
        time.sleep(2)

        # Kill Symphony
        # pylint: disable=subprocess-run-check
        subprocess.run(
            "taskkill /f /im symphony*", shell=True, capture_output=True
        )
        time.sleep(0.1)
        subprocess.run(
            "taskkill /f /im soffice*", shell=True, capture_output=True
        )
        time.sleep(0.5)
        # pylint: enable=subprocess-run-check

        # If outfile does not exist after the above, we probably have a
        # problem.
        if not outfile.is_file():
            raise SymphonyError(f"Conversion of {file} failed!")
