from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.dependencies import (
    get_avr_gcc_compiler,
    get_block_types_registry,
    get_programs_repository,
)
from app.domain import use_cases
from app.domain.adapters import AvrGccCompiler, MongoProgramsRepository
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
    UnsupportedMcuError,
)
from app.domain.models import (
    BlockTypesRegistry,
    Program,
    ProgramBuildResult,
)

from .schemas import (
    AddBlockRequestIn,
    ConnectBlocksRequestIn,
    CreateProgramRequestIn,
    ProgramResponse,
    UpdateBlockRequestIn,
    UpdateProgramRequestIn,
)

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("/", response_model=list[ProgramResponse])
async def get_programs(
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
) -> list[Program]:
    return await use_cases.get_all_programs(adapter)


@router.get("/{program_id}", response_model=ProgramResponse)
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


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ProgramResponse,
)
async def create_program(
    request_in: Annotated[CreateProgramRequestIn, Body(embed=True)],
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
    compiler: Annotated[AvrGccCompiler, Depends(get_avr_gcc_compiler)],
) -> Program:
    try:
        request = request_in.domain_model()
        return await use_cases.create_program(request, adapter, compiler)
    except DuplicatedProgramError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except UnsupportedMcuError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.put("/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: UUID,
    request_in: Annotated[UpdateProgramRequestIn, Body(embed=True)],
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
    compiler: Annotated[AvrGccCompiler, Depends(get_avr_gcc_compiler)],
) -> Program:
    try:
        request = request_in.domain_model(program_id)
        return await use_cases.update_program(request, adapter, compiler)
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except DuplicatedProgramError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except UnsupportedMcuError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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


@router.post(
    "/{program_id}/blocks",
    status_code=status.HTTP_201_CREATED,
    response_model=ProgramResponse,
)
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


@router.put("/{program_id}/blocks/{block_id}", response_model=ProgramResponse)
async def update_block(
    program_id: UUID,
    block_id: UUID,
    request_in: UpdateBlockRequestIn,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
    registry: Annotated[BlockTypesRegistry, Depends(get_block_types_registry)],
) -> Program:
    try:
        request = request_in.domain_model(program_id, block_id)
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


@router.patch("/{program_id}/connect", response_model=ProgramResponse)
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


@router.delete(
    "/{program_id}/connections/{connection_id}",
    response_model=ProgramResponse,
)
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


@router.post("/{program_id}/build")
async def build(
    program_id: UUID,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
    registry: Annotated[BlockTypesRegistry, Depends(get_block_types_registry)],
    compiler: Annotated[AvrGccCompiler, Depends(get_avr_gcc_compiler)],
) -> ProgramBuildResult:
    try:
        return await use_cases.build(program_id, adapter, registry, compiler)
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/{program_id}/clean-build", response_model=ProgramResponse)
async def clean_build(
    program_id: UUID,
    adapter: Annotated[
        MongoProgramsRepository,
        Depends(get_programs_repository),
    ],
) -> Program:
    try:
        return await use_cases.clean_build(program_id, adapter)
    except ProgramNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
