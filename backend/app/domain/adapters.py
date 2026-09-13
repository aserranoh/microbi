import subprocess
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Self
from uuid import UUID

from pydantic import TypeAdapter
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from .models import CompileOptions, Program

COLLECTION_NAME = "programs"


@dataclass(slots=True, kw_only=True)
class MongoProgramsRepository:
    uri: str
    database_name: str
    client: AsyncMongoClient = field(init=False)

    async def __aenter__(self) -> Self:
        self.client = AsyncMongoClient(self.uri)
        return self

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: type | None,
    ) -> None:
        await self.client.close()

    async def get_all(self) -> list[Program]:
        programs = await self._collection().find().to_list()
        return TypeAdapter(list[Program]).validate_python(programs)

    async def get_by_name(self, program_name: str) -> Program | None:
        return await self._read_program({"name": program_name})

    async def get_by_id(self, program_id: UUID) -> Program | None:
        return await self._read_program({"id": str(program_id)})

    async def create(self, program: Program) -> None:
        await self._collection().insert_one(
            TypeAdapter(Program).dump_python(program, mode="json"),
        )

    async def delete(self, program: Program) -> None:
        await self._collection().delete_one({"id": str(program.id)})

    async def update(self, program: Program) -> None:
        await self._collection().replace_one(
            {"id": str(program.id)},
            TypeAdapter(Program).dump_python(program, mode="json"),
        )

    def _collection(self) -> AsyncCollection:
        return self.client[self.database_name][COLLECTION_NAME]

    async def _read_program(self, query: dict[str, object]) -> Program | None:
        doc = await self._collection().find_one(query)
        if doc is None:
            return None
        return TypeAdapter(Program).validate_python(doc)


class AvrMcu(StrEnum):
    ATMEGA328P = "atmega328p"


@dataclass(frozen=True, slots=True, kw_only=True)
class AvrGccCompiler:
    lib_path: Path

    def get_mcus(self) -> list[str]:
        return [mcu.value for mcu in AvrMcu]

    def compile(self, cpp_code: str, options: CompileOptions) -> str:
        with TemporaryDirectory() as temp_dir:
            cpp_file = Path(temp_dir) / "main.cpp"
            cpp_file.write_text(cpp_code)
            elf_file = self._compile_and_link(
                cpp_file,
                options.mcu,
                self.lib_path,
            )
            hex_file = self._generate_hex(elf_file)
            return hex_file.read_text()

    def _compile_and_link(
        self,
        cpp_file: Path,
        mcu: str,
        lib_path: Path,
    ) -> Path:
        elf_file = cpp_file.parent / f"{cpp_file.stem}.elf"
        subprocess.run(
            [
                "avr-gcc",
                f"-mmcu={mcu}",
                "-o",
                elf_file.as_posix(),
                cpp_file.as_posix(),
                f"-I{lib_path.as_posix()}",
            ],
            check=True,
        )
        return elf_file

    def _generate_hex(self, elf_path: Path) -> Path:
        hex_file = elf_path.parent / f"{elf_path.stem}.hex"
        subprocess.run(
            [
                "avr-objcopy",
                "-O",
                "ihex",
                elf_path.as_posix(),
                hex_file.as_posix(),
            ],
            check=True,
        )
        return hex_file
