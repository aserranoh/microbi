from collections.abc import Iterable
from uuid import UUID

from .errors import (
    BlocksConnectionError,
    DuplicatedProgramError,
    ProgramNotFoundError,
)
from .models import (
    AddBlockRequest,
    Block,
    BlockType,
    BlockTypesRegistry,
    CodeGenerationError,
    CodeGenerationResult,
    ConnectBlocksRequest,
    PortDirection,
    Program,
    UpdateBlockRequest,
)
from .ports import ProgramsRepositoryPort

PROGRAM_TEMPLATE = """
{include_section}

using namespace microbi;

{declaration_section}

auto main() -> void
{{
    while (true) {{
{loop_section}
    }}
}}
"""


async def get_all_programs(
    programs_repo: ProgramsRepositoryPort,
) -> list[Program]:
    return await programs_repo.get_all()


async def create_program(
    program_name: str,
    programs_repo: ProgramsRepositoryPort,
) -> Program:
    program = await programs_repo.get_by_name(program_name)
    if program is not None:
        raise DuplicatedProgramError(program_name)
    new_program = Program(name=program_name)
    await programs_repo.create(new_program)
    return new_program


async def get_program(
    program_id: UUID,
    programs_repo: ProgramsRepositoryPort,
) -> Program:
    return await _get_program_or_raise(program_id, programs_repo)


async def delete_program(
    program_id: UUID,
    programs_repo: ProgramsRepositoryPort,
) -> None:
    program = await _get_program_or_raise(program_id, programs_repo)
    await programs_repo.delete(program)


async def add_block(
    request: AddBlockRequest,
    programs_repo: ProgramsRepositoryPort,
    blocks_registry: BlockTypesRegistry,
) -> Program:
    program = await _get_program_or_raise(request.program_id, programs_repo)
    block_type = blocks_registry.get_block_type(request.block_type_name)
    block_name = program.generate_block_name(request.block_type_name)
    block_config = block_type.get_default_configuration()

    new_block = Block(
        name=block_name,
        block_type=block_type.name,
        position=request.block_position,
        configuration=block_config,
    )
    program.add_block(new_block)
    await programs_repo.update(program)
    return program


async def remove_block(
    program_id: UUID,
    block_id: UUID,
    programs_repo: ProgramsRepositoryPort,
) -> Program:
    program = await _get_program_or_raise(program_id, programs_repo)
    block = program.get_block(block_id)
    program.remove_block(block)
    await programs_repo.update(program)
    return program


async def update_block(
    request: UpdateBlockRequest,
    programs_repo: ProgramsRepositoryPort,
    blocks_registry: BlockTypesRegistry,
) -> Program:
    program = await _get_program_or_raise(request.program_id, programs_repo)
    block = program.get_block(request.block_id)
    block_type = blocks_registry.get_block_type(block.block_type)
    if request.block_name:
        program.rename_block(block, request.block_name)
    if request.block_position is not None:
        block.position = request.block_position
    block_type.validate_configuration(request.block_config)
    block.update_configuration(request.block_config)
    await programs_repo.update(program)
    return program


async def connect_blocks(
    request: ConnectBlocksRequest,
    programs_repo: ProgramsRepositoryPort,
    blocks_registry: BlockTypesRegistry,
) -> Program:
    program = await _get_program_or_raise(request.program_id, programs_repo)
    source_block = program.get_block(request.source_block_id)
    target_block = program.get_block(request.target_block_id)
    source_block_type = blocks_registry.get_block_type(source_block.block_type)
    target_block_type = blocks_registry.get_block_type(target_block.block_type)
    source_port = source_block_type.get_port(request.source_port)
    target_port = target_block_type.get_port(request.target_port)

    if source_port.direction != PortDirection.OUTPUT:
        raise BlocksConnectionError(
            source_block=source_block.name,
            source_port=source_port.name,
            target_block=target_block.name,
            target_port=target_port.name,
            reason=(
                f"source port must be of direction `{PortDirection.OUTPUT}`"
            ),
        )
    if target_port.direction != PortDirection.INPUT:
        raise BlocksConnectionError(
            source_block=source_block.name,
            source_port=source_port.name,
            target_block=target_block.name,
            target_port=target_port.name,
            reason=(
                f"target port must be of direction `{PortDirection.INPUT}`"
            ),
        )
    if source_port.data_type != target_port.data_type:
        raise BlocksConnectionError(
            source_block=source_block.name,
            source_port=source_port.name,
            target_block=target_block.name,
            target_port=target_port.name,
            reason=(
                f"source port data type `{source_port.data_type}` "
                f"does not match "
                f"target port data type `{target_port.data_type}`"
            ),
        )

    program.connect(
        source=source_block,
        source_port=request.source_port,
        target=target_block,
        target_port=request.target_port,
    )
    await programs_repo.update(program)
    return program


async def remove_connection(
    program_id: UUID,
    connection_id: UUID,
    programs_repo: ProgramsRepositoryPort,
) -> Program:
    program = await _get_program_or_raise(program_id, programs_repo)
    connection = program.get_connection(connection_id)
    program.remove_connection(connection)
    await programs_repo.update(program)
    return program


async def get_all_block_types(
    blocks_registry: BlockTypesRegistry,
) -> list[BlockType]:
    return blocks_registry.get_all_block_types()


async def generate_code(
    program_id: UUID,
    programs_repo: ProgramsRepositoryPort,
    block_types_registry: BlockTypesRegistry,
) -> CodeGenerationResult:
    program = await _get_program_or_raise(program_id, programs_repo)
    block_impls = [
        block_types_registry.get_block_implementation(block.block_type)
        for block in program.blocks
    ]
    block_code_objects = [
        block_impl.generate_code(program, block)
        for block, block_impl in zip(program.blocks, block_impls, strict=True)
    ]
    blocks_code = zip(program.blocks, block_code_objects, strict=True)
    errors = [
        CodeGenerationError(
            block_type=block.block_type,
            block_name=block.name,
            block_uuid=block.id,
            error_message=error,
        )
        for block, code in blocks_code
        if code.has_errors()
        for error in code.errors
    ]

    return CodeGenerationResult(
        code=PROGRAM_TEMPLATE.format(
            include_section=_format(
                block_code.include for block_code in block_code_objects
            ),
            declaration_section=_format(
                block_code.declaration for block_code in block_code_objects
            ),
            loop_section=_format(
                (
                    block_code.main_loop_body
                    for block_code in block_code_objects
                ),
                indent=8,
            ),
        ),
        errors=errors,
    )


async def _get_program_or_raise(
    program_id: UUID, programs_repo: ProgramsRepositoryPort
) -> Program:
    program = await programs_repo.get_by_id(program_id)
    if program is None:
        raise ProgramNotFoundError(program_id)
    return program


def _format(code_lines: Iterable[str], indent: int = 0) -> str:
    indentation = " " * indent
    return "\n".join(f"{indentation}{line}" for line in code_lines)
