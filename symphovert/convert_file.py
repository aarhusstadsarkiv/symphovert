import pyperclip
try:
    import pyautogui
except Exception as e:
    raise ImportError(f"Failed to import pyautogui with error: {e}")

import subprocess
from subprocess import CalledProcessError
from pathlib import Path
from symphovert.exceptions import SymphonyError
import time
import os

def copypaste(str_to_copy: str) -> None:
    pyperclip.copy(f"{str_to_copy}")
    pyautogui.hotkey("ctrl", "v")
    time.sleep(5)
    pyautogui.press("enter")


def save_as(file: str) -> None:
    pyautogui.hotkey("ctrl", "shift", "s", interval=0.1)
    copypaste(file)


def symphony_convert(file: Path, outdir: Path, convert_to: str) -> None:
    # Initialise variables
    outfile: Path = outdir / f"{file.stem}.{convert_to}"

    # If outfile exists, delete it first.
    if outfile.is_file():
        outfile.unlink()

    # Open IBM Symphony and do unholy things with pyautogui
    try:
        subprocess.run(
            "symphony.exe", shell=True, check=True, capture_output=True
        )
    except CalledProcessError as error:
        error_msg = error.stderr.strip().decode()
        raise SymphonyError(
            f"Execution of IBM Symphony failed with error: {error_msg}"
        )
    else:
        # Wait a bit, then open the file
        time.sleep(2)
        pyautogui.hotkey("ctrl", "o", interval=0.5)
        time.sleep(1)
        if "ROOTPATH" in os.environ:
            absolute_file_path = Path(os.environ["ROOTPATH"]) / file
        else:
            absolute_file_path =  file
        copypaste(str(absolute_file_path))
        time.sleep(1)

        # Symphony opens an extra menu when ctrl+o is used for... reasons.
        # Esc closes it.
        pyautogui.hotkey("escape")
        time.sleep(2)
       
        
        # Save the file as ODT.
        save_as(str(outfile))
        time.sleep(2)

        # Kill Symphony
        # pylint: disable=subprocess-run-check
        subprocess.run(
            "taskkill /f /im symphony*", shell=True, capture_output=True
        )
        time.sleep(0.5)
        subprocess.run(
            "taskkill /f /im soffice*", shell=True, capture_output=True
        )
        time.sleep(1)
        # pylint: enable=subprocess-run-check

        # If outfile does not exist after the above, we probably have a
        # problem.
        if not outfile.is_file():
            raise SymphonyError(f"Conversion of {file} failed!")



if __name__ == "__main__":
    input_file = Path("E:\\Staging\\Processing\\AVID.AARS.85.1\\OriginalDocuments\\docCollection1\\40\\Mødeindkaldelse til parterne.lwp")
    symphony_convert(input_file, input_file.parent, "odt")