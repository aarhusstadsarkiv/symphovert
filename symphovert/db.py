# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
# from typing import Any
# from typing import Dict

from typing import Dict, List
from typing import Set
from uuid import UUID

import sqlalchemy as sql
from symphovert.ArchiveFileRel import ArchiveFile
from databases import Database
from pydantic import parse_obj_as
from pydantic import ValidationError
from sqlalchemy.engine import Engine
from sqlalchemy.sql.expression import TextClause
from sqlalchemy_views import CreateView
from sqlalchemy_views import DropView

from convertool.exceptions import FileParseError
import json

# -----------------------------------------------------------------------------
# Database class
# -----------------------------------------------------------------------------


class FileDB(Database):
    """File database"""

    sql_meta = sql.MetaData()
    converted_files = sql.Table(
        "_ConvertedFiles",
        sql_meta,
        sql.Column(
            "file_id",
            sql.Integer,
            sql.ForeignKey("Files.id"),
            nullable=False,
        ),
        sql.Column("uuid", sql.Unicode, nullable=False),
        extend_existing=True,
    )
    not_converted = sql.Table("_NotConverted", sql_meta)

    file_template_map = sql.Table(
        "ReplacedFiles",
        sql_meta,
        sql.Column(
            "uuid", sql.Unicode, sql.ForeignKey("Files.uuid"), nullable=False
        ),
        sql.Column(
            "Template_specifier",
            sql.Enum(
                "Damaged",
                "Empty",
                "Not_Convertable",
                "Not_Preservable",
                "Password_Protected",
            ),
            nullable=False,
        ),
        extend_existing=True,
    )

    def __init__(self, url: str) -> None:
        super().__init__(url)
        self.engine = sql.create_engine(
            url, connect_args={"check_same_thread": False}
        )

        # Table reflection
        self.sql_meta.reflect(bind=self.engine)
        self.files = self.sql_meta.tables["Files"]
        self.converted_files.create(self.engine, checkfirst=True)
        self.file_template_map.create(self.engine, checkfirst=True)

        # Create _NotConverted view
        view_def = sql.text(
            "SELECT f.id, f.uuid, relative_path, puid, signature, warning "
            "FROM Files AS f "
            "LEFT JOIN _ConvertedFiles AS c "
            "ON f.uuid = c.uuid WHERE c.uuid IS NULL"
        )
        create_view(self.not_converted, view_def, self.engine)

    async def get_files(self) -> List[ArchiveFile]:
        query = self.files.select()
        rows = await self.fetch_all(query)
        try:
            files = parse_obj_as(List[ArchiveFile], rows)
        except ValidationError:
            raise FileParseError("Failed to parse files as ArchiveFiles.")
        else:
            return files

    async def get_lotus_smartsuite_files(self) -> List[ArchiveFile]:
        with open("convert_map.json", "r") as read_file:
            convert_map: Dict[str, str] = json.load(read_file)
        
        query = "SELECT * FROM Files WHERE Files.puid IN ('aca-fmt/1', 'fmt/340', 'fmt/1216', 'x-fmt/340');"
        rows = await self.fetch_all(query=query)
        try:
            files = parse_obj_as(List[ArchiveFile], rows)
        except ValidationError:
            raise FileParseError("Failed to parse files as ArchiveFiles.")
        else:
            return files

    async def get_pdf_1_7_files(self) -> List[ArchiveFile]:
        query = self.files.select().where(self.files.c.puid == "fmt/276")
        rows = await self.fetch_all(query)
        try:
            files = parse_obj_as(List[ArchiveFile], rows)
        except ValidationError:
            # print(rows)
            raise FileParseError("Failed to parse files as ArchiveFiles.")
        else:
            return files

    async def update_status(self, uuid: UUID) -> None:
        async with self.transaction():
            get_file_id = self.files.select().where(
                self.files.c.uuid == str(uuid)
            )
            file_id = await self.fetch_val(get_file_id, column="id")
            exists = await self.check_status(uuid)
            if not exists:
                insert_file = self.converted_files.insert()
                insert_values = {"file_id": file_id, "uuid": str(uuid)}
                await self.execute(insert_file, insert_values)
            else:
                return

    async def update_template_status(self, uuid: UUID, specifier: str) -> None:
        async with self.transaction():

            exists = await self.check_template_status(uuid)
            if not exists:
                insert_file = self.file_template_map.insert()
                insert_values = {
                    "uuid": str(uuid),
                    "Template_specifier": specifier,
                }
                await self.execute(insert_file, insert_values)
            else:
                return

    async def check_status(self, uuid: UUID) -> bool:
        conv_files = self.converted_files
        select_uuid = conv_files.select().where(conv_files.c.uuid == str(uuid))
        check = await self.fetch_one(select_uuid)
        return bool(check)

    async def check_template_status(self, uuid: UUID) -> bool:
        replaced_files = self.file_template_map
        select_uuid = replaced_files.select().where(
            replaced_files.c.uuid == str(uuid)
        )
        check = await self.fetch_one(select_uuid)
        return bool(check)

    async def converted_uuids(self) -> Set[UUID]:
        conv_files = self.converted_files
        query = conv_files.select()
        rows = await self.fetch_all(query)
        return {UUID(row["uuid"]) for row in rows}


# -----------------------------------------------------------------------------
# View Creation Utility
# -----------------------------------------------------------------------------


def create_view(
    table: sql.Table, definition: TextClause, engine: Engine
) -> None:
    view_drop = DropView(table, if_exists=True)
    view_create = CreateView(table, definition)
    engine.execute(view_drop)
    engine.execute(view_create)
