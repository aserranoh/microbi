from dataclasses import dataclass, field
from typing import Self
from uuid import UUID

from pydantic import TypeAdapter
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from .models import Program

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
