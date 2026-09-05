from collections.abc import AsyncGenerator

from fastapi import Request

from app.domain.adapters import MongoProgramsRepository
from app.domain.models import BlockTypesRegistry


async def get_programs_repository() -> AsyncGenerator[MongoProgramsRepository]:
    adapter = MongoProgramsRepository(
        uri="mongodb://root:root@localhost:27017", database_name="microbi"
    )
    async with adapter:
        yield adapter


async def get_block_types_registry(request: Request) -> BlockTypesRegistry:
    return request.app.state.block_types_registry
