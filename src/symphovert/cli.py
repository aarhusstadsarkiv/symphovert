from logging import ERROR
from logging import INFO
from os import PathLike
from pathlib import Path

import click
from acacore.database import FilesDB
from acacore.models.event import Event
from acacore.models.file import MasterFile
from acacore.utils.click import end_program
from acacore.utils.click import start_program
from acacore.utils.helpers import ExceptionManager

from . import __version__
from .convert import symphony_convert
from .exceptions import SymphonyError

TOOL_NAME = "symphovert"


@click.command("symphovert", no_args_is_help=True)
@click.argument("avid", type=click.Path(exists=True, file_okay=False, writable=True), required=True)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx: click.Context, avid: str | PathLike[str]):
    avid = Path(avid).absolute()
    db_path = avid.joinpath("_metadata", "avid.db")
    original_docs_dir = avid.joinpath("OriginalDocuments")
    master_docs_dir = avid.joinpath("MasterDocuments")

    if not db_path.is_file():
        raise click.BadParameter(f"Database is not present at {db_path}.", ctx)

    with FilesDB(db_path) as db:
        if not db.is_initialised():
            raise click.BadParameter("Database is not initialised.", ctx)

        logger, _ = start_program(ctx, db, __version__)

        with ExceptionManager(BaseException) as exception:
            for file in db.original_files.select("processed is false and action = 'convert'"):
                if not file.action_data.convert:
                    continue
                if file.action_data.convert.tool != TOOL_NAME:
                    continue

                Event.from_command(ctx, "convert", file).log(INFO, logger, name=file.name)

                file.root = avid
                master_file_path = master_docs_dir.joinpath(file.get_absolute_path().relative_to(original_docs_dir))
                master_file_path = master_file_path.with_suffix("." + file.action_data.convert.output.lstrip("."))

                if master_file := db.master_files[{"relative_path": master_file_path.relative_to(avid).as_posix()}]:
                    Event.from_command(ctx, "exists", master_file).log(INFO, logger, name=master_file.name)
                    continue

                try:
                    symphony_convert(file.get_absolute_path(), master_file_path)
                except SymphonyError as e:
                    Event.from_command(ctx, "error", file).log(ERROR, logger, error=repr(e))
                    continue

                master_file = MasterFile.from_file(master_file_path, avid, {"original_uuid": file.uuid, "sequence": 0})

                db.master_files.insert(master_file)
                file.processed = True
                db.original_files.update(file)
                db.commit()

                Event.from_command(ctx, "output", master_file).log(INFO, logger, name=master_file.name)

        end_program(ctx, db, exception, False, logger)
