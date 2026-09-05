from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_block_types_registry, get_programs_repository
from app.domain import use_cases
from app.domain.adapters import MongoProgramsRepository
from app.domain.errors import (
    BlockNotFoundError,
    BlocksConnectionError,
    BlockTypeNotFoundError,
    ConnectionNotFoundError,
    DuplicatedBlockNameError,
    DuplicatedProgramError,
    PortNotFoundError,
    ProgramNotFoundError,
    UnknownBlockConfigurationError,
)
from app.domain.models import (
    AddBlockRequest,
    BlockTypesRegistry,
    CodeGenerationResult,
    ConnectBlocksRequest,
    Program,
    UpdateBlockRequest,
)

router = APIRouter(prefix="/programs", tags=["programs"])


class PositionIn(BaseModel):
    x: float
    y: float


class AddBlockRequestIn(BaseModel):
    program_id: UUID
    block_type_name: str = Field(min_length=1)
    block_position: PositionIn

    def domain_model(self) -> AddBlockRequest:
        return AddBlockRequest(**self.model_dump())


class UpdateBlockRequestIn(BaseModel):
    program_id: UUID
    block_name: str | None = Field(
        default=None,
        pattern=r"^[_a-zA-Z][_a-zA-Z0-9]*$",
    )
    block_position: PositionIn | None = None
    block_config: dict[str, object] | None = None

    def domain_model(self, block_id: UUID) -> UpdateBlockRequest:
        return UpdateBlockRequest(
            **self.model_dump(exclude_unset=True),
            block_id=block_id,
        )


class ConnectBlocksRequestIn(BaseModel):
    source_block_id: UUID
    source_port: str
    target_block_id: UUID
    target_port: str

    def domain_model(self, program_id: UUID) -> ConnectBlocksRequest:
        return ConnectBlocksRequest(
            program_id=program_id,
            **self.model_dump(exclude_unset=True),
        )


@router.get("/")
async def get_programs(
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
) -> list[Program]:
    return await use_cases.get_all_programs(adapter)


@router.get("/{program_id}")
async def get_program(
    program_id: UUID,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
) -> Program:
    try:
        return await use_cases.get_program(program_id, adapter)
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_program(
    program_name: Annotated[str, Body(min_length=1, embed=True)],
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
) -> Program:
    try:
        return await use_cases.create_program(program_name, adapter)
    except DuplicatedProgramError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    program_id: UUID,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
) -> None:
    try:
        await use_cases.delete_program(program_id, adapter)
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/{program_id}/blocks", status_code=status.HTTP_201_CREATED)
async def add_block(
    request_in: AddBlockRequestIn,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
    registry: Annotated[BlockTypesRegistry, Depends(get_block_types_registry)],
) -> Program:
    try:
        request = request_in.domain_model()
        return await use_cases.add_block(request, adapter, registry)
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except BlockTypeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.delete(
    "/{program_id}/blocks/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_block(
    program_id: UUID,
    block_id: UUID,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
) -> None:
    try:
        await use_cases.remove_block(program_id, block_id, adapter)
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except BlockNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.put("/{program_id}/blocks/{block_id}")
async def update_block(
    block_id: UUID,
    request_in: UpdateBlockRequestIn,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
    registry: Annotated[BlockTypesRegistry, Depends(get_block_types_registry)],
) -> Program:
    try:
        request = request_in.domain_model(block_id)
        return await use_cases.update_block(request, adapter, registry)
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except BlockNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except DuplicatedBlockNameError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except UnknownBlockConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.patch("/{program_id}/connect")
async def connect_blocks(
    program_id: UUID,
    request_in: ConnectBlocksRequestIn,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
    registry: Annotated[BlockTypesRegistry, Depends(get_block_types_registry)],
) -> Program:
    try:
        request = request_in.domain_model(program_id)
        return await use_cases.connect_blocks(request, adapter, registry)
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except BlockNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PortNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except BlocksConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/{program_id}/connections/{connection_id}")
async def remove_connection(
    program_id: UUID,
    connection_id: UUID,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
) -> Program:
    try:
        return await use_cases.remove_connection(
            program_id,
            connection_id,
            adapter,
        )
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ConnectionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/{program_id}/generate-code")
async def generate_code(
    program_id: UUID,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
    registry: Annotated[BlockTypesRegistry, Depends(get_block_types_registry)],
) -> CodeGenerationResult:
    try:
        return await use_cases.generate_code(program_id, adapter, registry)
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
