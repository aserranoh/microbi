from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_block_types_registry
from app.domain import use_cases
from app.domain.models import (
    BlockType,
    BlockTypesRegistry,
)

from .schemas import BlockTypeResponse

router = APIRouter(prefix="/block-types", tags=["block-types"])


@router.get("/", response_model=list[BlockTypeResponse])
async def get_block_types(
    registry: Annotated[BlockTypesRegistry, Depends(get_block_types_registry)],
) -> list[BlockType]:
    return await use_cases.get_all_block_types(registry)
