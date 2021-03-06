"""Tool for converting Lotus Word Pro and Lotus 123 Spreadsheet files
to Open Document Format files using IBM Symphony and PyAutoGUI.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
import time
from logging import Logger
from pathlib import Path
from typing import List

import click
from pydantic import BaseModel
from symphovert.convert import symphony_convert

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

ACCEPTED_OUT = ["odt", "ods", "odp"]

# -----------------------------------------------------------------------------
# FileConv data model
# -----------------------------------------------------------------------------


class FileConv(BaseModel):
    files: List[Path]
    outdir: Path


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.argument(
    "files", type=click.Path(exists=True, file_okay=True, resolve_path=True)
)
@click.argument(
    "outdir", type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
@click.option(
    "--to",
    "to_",
    type=click.Choice(ACCEPTED_OUT, case_sensitive=False),
    default="odt",
    help="File format to convert to. Default: ODT.",
)
@click.option(
    "--parents",
    default=2,
    help="Number of parent directories to use for output name. Default: 0",
)
def cli(files: Path, outdir: Path, to_: str, parents: int) -> None:
    files = Path(files)
    outdir = Path(outdir)
    file_list = get_files(files)
    # Set up logging
    logger: Logger = log_setup(
        log_name="Conversion",
        log_file=outdir / f"_symphovert_{time.time()}.log",
    )
    errs: int = 0
    for file in file_list:
        try:
            new_outdir = create_outdir(file, outdir, parents)
            symphony_convert(file, new_outdir, to_)
        except Exception as error:
            errs += 1
            logger.warning(f"{error}")
    if errs > 0:
        raise click.ClickException(
            f"symphovert finished conversion with {errs} errors."
        )


# -----------------------------------------------------------------------------
# Auxiliary functions
# -----------------------------------------------------------------------------


def get_files(files: Path) -> List[Path]:
    if files.is_file():
        return [Path(line.rstrip()) for line in files.open(encoding="utf-8")]
    elif files.is_dir():
        return [path for path in files.rglob("*") if path.is_file()]
    else:
        raise ValueError("No files found!")


def create_outdir(file: Path, outdir: Path, parents: int = 0) -> Path:
    for i in range(parents, 0, -1):
        try:
            subdir = Path(f"{file}").parent.parts[-i]
        except IndexError:
            err_msg = f"Parent index {parents} out of range for {file}"
            raise IndexError(err_msg)
        else:
            outdir = outdir.joinpath(subdir)

    # Create the resulting output directory
    outdir.mkdir(parents=True, exist_ok=True)

    return outdir


def log_setup(log_name: str, log_file: Path, mode: str = "w") -> Logger:
    logger = logging.getLogger(log_name)
    file_handler = logging.FileHandler(log_file, mode)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%H:%M:%S"
        )
    )
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    return logger
