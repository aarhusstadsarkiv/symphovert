"""Tool for converting Lotus Word Pro and Lotus 123 Spreadsheet files
to Open Document Format files using IBM Symphony and PyAutoGUI.
"""
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import asyncio
from functools import wraps
from pathlib import Path
from typing import Any
from typing import Callable
from typing import List

import click
from acamodels import ArchiveFile
from click.core import Context as ClickContext

from symphovert.convert import FileConv
from symphovert.convert import FileDB

# -----------------------------------------------------------------------------
# Auxiliary functions
# -----------------------------------------------------------------------------


def coro(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(func(*args, **kwargs))

    return wrapper


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
@click.pass_context
@coro
async def cli(ctx: ClickContext, files: Path, outdir: Path) -> None:
    """Convert files from a digiarch generated file database.
    OUTDIR specifies the directory in which to output converted files.
    It must be an existing directory."""

    try:
        file_db: FileDB = FileDB(f"sqlite:///{files}")
    except Exception:
        raise click.ClickException(f"Failed to load {files} as a database.")
    else:
        click.secho("Collecting files...", bold=True)
        files_: List[ArchiveFile] = await file_db.get_files()
        if not files_:
            raise click.ClickException("Database is empty. Aborting.")

    ctx.obj = FileConv(files=files_, db=file_db, out_dir=outdir)


@cli.command()
@click.pass_obj
@coro
async def main(file_conv: FileConv) -> None:
    """Convert files to their Main Archival version."""
    try:
        await file_conv.convert()
    except Exception as error:
        raise click.ClickException(str(error))
