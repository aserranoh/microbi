
from uuid import UUID


class DomainError(Exception):
    pass


class BlockNotFoundError(DomainError):

    def __init__(self, block_ref) -> None:
        msg = f"block `{block_ref}` not found"
        super().__init__(msg)


class BlockTypeNotFoundError(DomainError):

    def __init__(self, block_type_name: str) -> None:
        msg = f"block type `{block_type_name}` not found"
        super().__init__(msg)


class ConnectionNotFoundError(DomainError):

    def __init__(self, connection_id: UUID) -> None:
        msg = f"connection `{connection_id}` not found"
        super().__init__(msg)


class DuplicatedBlockNameError(DomainError):

    def __init__(self, block_name: str) -> None:
        msg = f"block `{block_name}` already exists"
        super().__init__(msg)


class DuplicatedProgramError(DomainError):

    def __init__(self, program_name: str) -> None:
        msg = f"program `{program_name}` already exists"
        super().__init__(msg)


class InvalidBlockConfigurationTypeError(DomainError):

    def __init__(self, field_name: str, value: object, type_: type[object]) -> None:
        msg = f"configuration element `{field_name}={value}` has wrong type: expected `{type_}`"
        super().__init__(msg)


class ProgramNotFoundError(DomainError):

    def __init__(self, program_ref: UUID | str) -> None:
        msg = f"program `{program_ref}` not found"
        super().__init__(msg)


class UnknownBlockConfigurationError(DomainError):

    def __init__(self, block_type_name: str, field_name: str) -> None:
        msg = f"configuration field `{field_name}` unknown for block `{block_type_name}`"
        super().__init__(msg)