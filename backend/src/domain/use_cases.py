
from uuid import UUID

from .errors import DuplicatedProgramError, ProgramNotFoundError
from .models import AddBlockRequest, Block, BlockTypesRegistry, Program, UpdateBlockRequest
from .ports import ProgramsRepositoryPort


def get_all_programs(programs_repo: ProgramsRepositoryPort) -> list[Program]:
    return programs_repo.get_all()

def create_program(program_name: str, programs_repo: ProgramsRepositoryPort) -> Program:
    program = programs_repo.get_by_name(program_name)
    if program is not None:
        raise DuplicatedProgramError(program_name)
    return programs_repo.create(program_name)

def get_program(program_id: UUID, programs_repo: ProgramsRepositoryPort) -> Program:
    return _get_program_or_raise(program_id, programs_repo)

def delete_program(program_id: UUID, programs_repo: ProgramsRepositoryPort) -> None:
    program = _get_program_or_raise(program_id, programs_repo)
    programs_repo.delete(program)

def add_block(
    request: AddBlockRequest,
    programs_repo: ProgramsRepositoryPort,
    blocks_registry: BlockTypesRegistry,
) -> Program:
    program = _get_program_or_raise(request.program_id, programs_repo)
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
    programs_repo.update(program)
    return program

def remove_block(program_id: UUID, block_id: UUID, programs_repo: ProgramsRepositoryPort) -> Program:
    program = _get_program_or_raise(program_id, programs_repo)
    block = program.get_block(block_id)
    program.remove_block(block)
    programs_repo.update(program)
    return program

def update_block(
    request: UpdateBlockRequest,
    programs_repo: ProgramsRepositoryPort,
    blocks_registry: BlockTypesRegistry,
) -> Program:
    program = _get_program_or_raise(request.program_id, programs_repo)
    block = program.get_block(request.block_id)
    block_type = blocks_registry.get_block_type(block.block_type)
    if request.block_name:
        program.rename_block(request.block_name)
    block_type.validate_configuration(request.configuration)
    block.update_configuration(request.configuration)
    programs_repo.update(program)
    return program

def connect_blocks(request: ConnectionRequest, programs_repo: ProgramsRepositoryPort) -> Program:
    program = _get_program_or_raise(request.program_id, programs_repo)
    
    programs_repo.update(program)
    return program

def remove_connection(program_id: UUID, connection_id: UUID, programs_repo: ProgramsRepositoryPort) -> Program:
    program = _get_program_or_raise(program_id, programs_repo)
    connection = program.get_connection(connection_id)
    program.remove_connection(connection)
    programs_repo.update(program)

def _get_program_or_raise(program_id: UUID, programs_repo: ProgramsRepositoryPort) -> Program:
    program = programs_repo.get_by_id(program_id)
    if program is None:
        raise ProgramNotFoundError(program_id)
    return program
