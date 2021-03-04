"""Tool for converting Lotus SmartSuite files to Open Document format.
"""
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import json
import subprocess
import time
from logging import Logger
from pathlib import Path
from subprocess import CalledProcessError
from typing import Dict
from typing import List
from typing import Optional

import pyperclip
import tqdm
from acamodels import ACABase
from acamodels import ArchiveFile
from convertool.core.utils import log_setup
from convertool.database import FileDB

from symphovert.exceptions import SymphonyError

try:
    import pyautogui
except Exception as e:
    raise ImportError(f"Failed to import pyautogui with error: {e}")

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------
pyautogui.PAUSE = 1
pyautogui.FAILSAFE = False
PARENT_DIR: Path = Path(__file__).parent

# -----------------------------------------------------------------------------
# FileConv class
# -----------------------------------------------------------------------------


class FileConv(ACABase):
    files: List[ArchiveFile]
    db: FileDB
    out_dir: Path

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def conv_map() -> Dict[str, str]:
        map_file = PARENT_DIR / "convert_map.json"
        with map_file.open(encoding="utf-8") as f:
            c_map: Dict[str, str] = json.load(f)
            return c_map

    async def convert(self) -> None:
        # Initialise variables
        err_count: int = 0
        convert_to: Optional[str]
        converted_uuids = await self.db.converted_uuids()
        to_convert: List[ArchiveFile] = []

        # Set up logging
        logger: Logger = log_setup(
            log_name="Conversion",
            log_file=Path(self.out_dir) / "symphovert.log",
        )

        for f in self.files:
            # Create all output directories
            (self.out_dir / f.aars_path.parent).mkdir(
                parents=True, exist_ok=True
            )
            if f.puid in self.conv_map() and f.uuid not in converted_uuids:
                to_convert.append(f)

        # Start conversion.
        logger.info(
            f"Started conversion of {len(to_convert)} files "
            f"from {self.db.url} to {self.out_dir}"
        )

        for file in tqdm.tqdm(
            to_convert, desc="Converting files", unit="file"
        ):
            # Define output directory
            file_out: Path = self.out_dir / file.aars_path.parent

            # Convert info
            convert_to = self.conv_map().get(file.puid)

            if convert_to in ["odt", "ods", "odp"]:
                logger.info(f"Starting conversion of {file.path}")

                try:
                    symphony_convert(file.path, file_out, convert_to)
                except Exception as error:
                    logger.warning(f"Failed to convert {file.path}: {error}")
                    err_count += 1
                else:
                    await self.db.update_status(file.uuid)
                    logger.info(f"Converted {file.path} successfully.")

        # We are done! Log before we finish.
        logger.info(
            f"Finished conversion of {len(to_convert)} files "
            f"with {err_count} issues."
        )


# -----------------------------------------------------------------------------
# Symphony conversion
# -----------------------------------------------------------------------------


def copypaste(str_to_copy: str) -> None:
    pyperclip.copy(f"{str_to_copy}")
    pyautogui.hotkey("ctrl", "v")
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
        copypaste(str(file))
        time.sleep(0.5)

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
