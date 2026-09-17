import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol, Self
from uuid import UUID, uuid4

from .errors import (
    BlockNotFoundError,
    BlocksConnectionError,
    BlockTypeNotFoundError,
    ConnectionNotFoundError,
    DuplicatedBlockNameError,
    InvalidBlockConfigurationTypeError,
    PortNotFoundError,
    UnknownBlockConfigurationError,
)


def ensure_non_empty_name(name: str) -> None:
    if not name.strip():
        err_msg = "empty name"
        raise ValueError(err_msg)


def now_utc() -> datetime:
    return datetime.now(UTC)


class PortDirection(StrEnum):
    INPUT = "input"
    OUTPUT = "output"


class DataType(StrEnum):
    BOOL = "bool"
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"


class FieldType(StrEnum):
    INTEGER = "integer"
    ENUM = "enum"


class ArtifactType(StrEnum):
    CPP = "cpp"
    ASM = "asm"
    HEX = "hex"


@dataclass(frozen=True, slots=True, kw_only=True)
class Position:
    x: float
    y: float


@dataclass(frozen=True, slots=True, kw_only=True)
class Port:
    name: str
    direction: PortDirection
    data_type: DataType

    def __post_init__(self) -> None:
        ensure_non_empty_name(self.name)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigurationField[T]:
    name: str
    type: FieldType
    default: T

    def __post_init__(self) -> None:
        ensure_non_empty_name(self.name)

    @property
    def python_type(self) -> type[T]:
        return type(self.default)


@dataclass(frozen=True, slots=True, kw_only=True)
class IntegerConfiguration(ConfigurationField[int]):
    type: FieldType = field(init=False, default=FieldType.INTEGER)
    min: int | None = None
    max: int | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self._check_interval_coherent()
        self._check_default_in_interval()

    def _check_interval_coherent(self) -> None:
        if self.min is None or self.max is None:
            return
        if self.min > self.max:
            err_msg = "min has to be lower than max"
            raise ValueError(err_msg)

    def _check_default_in_interval(self) -> None:
        if self.min is not None and self.default < self.min:
            err_msg = "default cannot be lower than min"
            raise ValueError(err_msg)
        if self.max is not None and self.default > self.max:
            err_msg = "default cannot be grater than max"
            raise ValueError(err_msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class EnumConfiguration(ConfigurationField[str]):
    type: FieldType = field(init=False, default=FieldType.ENUM)
    choices: tuple[str, ...]
    default: str

    def __post_init__(self) -> None:
        super().__post_init__()
        self._check_choices_not_empty()
        self._check_choices_uniqueness()
        self._check_default_in_choices()

    def _check_choices_not_empty(self) -> None:
        if not self.choices:
            err_msg = "empty choices"
            raise ValueError(err_msg)

    def _check_choices_uniqueness(self) -> None:
        if len(self.choices) != len(set(self.choices)):
            err_msg = "repeated choices"
            raise ValueError(err_msg)

    def _check_default_in_choices(self) -> None:
        if self.default not in self.choices:
            err_msg = "default not in choices"
            raise ValueError(err_msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class BlockType:
    name: str
    description: str
    ports: tuple[Port, ...]
    configuration: tuple[ConfigurationField, ...]

    def __post_init__(self) -> None:
        ensure_non_empty_name(self.name)

    def get_default_configuration(self) -> dict[str, object]:
        return {config.name: config.default for config in self.configuration}

    def get_port(self, port_name: str) -> Port:
        for port in self.ports:
            if port.name == port_name:
                return port
        raise PortNotFoundError(port_name)

    def validate_configuration(self, configuration: dict[str, object]) -> None:
        config_by_name = {field.name: field for field in self.configuration}
        for key, value in configuration.items():
            try:
                field = config_by_name[key]
            except KeyError:
                raise UnknownBlockConfigurationError(self.name, key) from None
            if not isinstance(value, field.python_type):
                raise InvalidBlockConfigurationTypeError(
                    key, value, field.python_type
                )


@dataclass(slots=True, kw_only=True)
class Block:
    id: UUID = field(default_factory=uuid4)
    name: str
    block_type: str
    position: Position
    configuration: dict[str, object]

    def update_configuration(self, new_config: dict[str, object]) -> bool:
        previous_config = self.configuration.copy()
        self.configuration.update(new_config)
        return previous_config != self.configuration


@dataclass(frozen=True, slots=True, kw_only=True)
class PortReference:
    block_id: UUID
    port_name: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Connection:
    id: UUID = field(default_factory=uuid4)
    source: PortReference
    target: PortReference


@dataclass(frozen=True, slots=True, kw_only=True)
class ProgramArtifact:
    type: ArtifactType
    mcu: str
    program_revision: int
    generated_at: datetime = field(default_factory=now_utc)
    contents: str


@dataclass(slots=True, kw_only=True)
class Program:
    id: UUID = field(default_factory=uuid4)
    name: str
    blocks: list[Block] = field(default_factory=list[Block])
    connections: list[Connection] = field(default_factory=list[Connection])
    mcu: str = ""
    revision: int = 1
    modified_at: datetime = field(default_factory=now_utc)
    artifacts: list[ProgramArtifact] = field(
        default_factory=list[ProgramArtifact],
    )

    def add_block(self, block: Block) -> None:
        self.blocks.append(block)
        self._update_revision()

    def connect(
        self,
        source: Block,
        source_port: str,
        target: Block,
        target_port: str,
    ) -> None:
        existing_connection = next(
            (
                conn
                for conn in self.connections
                if conn.target.block_id == target.id
                and conn.target.port_name == target_port
            ),
            None,
        )
        if existing_connection is not None:
            raise BlocksConnectionError(
                source_block=source.name,
                source_port=source_port,
                target_block=target.name,
                target_port=target_port,
                reason="target port already connected",
            )
        src_ref = PortReference(block_id=source.id, port_name=source_port)
        tgt_ref = PortReference(block_id=target.id, port_name=target_port)
        self.connections.append(Connection(source=src_ref, target=tgt_ref))
        self._update_revision()

    def generate_block_name(self, root: str) -> str:
        root = re.sub(r"[^a-zA-Z0-9_]", "_", root)
        root = re.sub(r"^[0-9]+", "", root)
        root = root.lower()
        if not root:
            root = "_"

        names = set(block.name for block in self.blocks)
        suffix = 1
        while True:
            name = f"{root}{suffix}"
            if name not in names:
                return name
            suffix += 1

    def get_block(self, block_id: UUID) -> Block:
        block = next(
            (block for block in self.blocks if block.id == block_id), None
        )
        if block is None:
            raise BlockNotFoundError(block_id)
        return block

    def get_connection(self, connection_id: UUID) -> Connection:
        conn = next(
            (conn for conn in self.connections if conn.id == connection_id),
            None,
        )
        if conn is None:
            raise ConnectionNotFoundError(connection_id)
        return conn

    def remove_block(self, block: Block) -> None:
        self.connections = [
            connection
            for connection in self.connections
            if connection.source.block_id != block.id
            and connection.target.block_id != block.id
        ]
        self.blocks.remove(block)
        self._update_revision()

    def remove_connection(self, connection: Connection) -> None:
        self.connections.remove(connection)
        self._update_revision()

    def rename_block(self, block: Block, new_name: str) -> bool:
        repeated = next(
            (b for b in self.blocks if b != block and b.name == new_name),
            None,
        )
        if repeated is not None:
            raise DuplicatedBlockNameError(new_name)
        if block.name != new_name:
            block.name = new_name
            return True
        return False

    def change_block_position(
        self,
        block: Block,
        new_position: Position,
    ) -> bool:
        if block.position != new_position:
            block.position = new_position
            return True
        return False

    def update_block_configuration(
        self,
        block: Block,
        new_config: dict[str, object],
    ) -> bool:
        return block.update_configuration(new_config)

    def who_connects_to(self, port_ref: PortReference) -> PortReference | None:
        connection = next(
            (conn for conn in self.connections if conn.target == port_ref),
            None,
        )
        if connection is None:
            return None
        return connection.source

    def get_artifact(
        self,
        artifact_type: ArtifactType,
    ) -> ProgramArtifact | None:
        return next(
            (
                artifact
                for artifact in self.artifacts
                if artifact.type == artifact_type
            ),
            None,
        )

    def add_artifact(
        self,
        artifact_type: ArtifactType,
        contents: str,
    ) -> ProgramArtifact:
        artifact = ProgramArtifact(
            type=artifact_type,
            mcu=self.mcu,
            program_revision=self.revision,
            contents=contents,
        )
        self.artifacts.append(artifact)
        return artifact

    def is_outdated(self, artifact: ProgramArtifact) -> bool:
        return artifact.program_revision < self.revision

    def _update_revision(self) -> None:
        self.modified_at = now_utc()
        artifact_revision = max(
            (artifact.program_revision for artifact in self.artifacts),
            default=0,
        )
        if artifact_revision == self.revision:
            self.revision += 1


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateProgramRequest:
    name: str
    mcu: str


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateProgramRequest:
    id: UUID
    name: str | None = None
    mcu: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AddBlockRequest:
    program_id: UUID
    block_type_name: str
    block_position: Position


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateBlockRequest:
    program_id: UUID
    block_id: UUID
    block_name: str | None = None
    block_position: Position | None = None
    block_config: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectBlocksRequest:
    program_id: UUID
    source_block_id: UUID
    source_port: str
    target_block_id: UUID
    target_port: str


@dataclass(frozen=True, slots=True, kw_only=True)
class BlockCodeGenerationError:
    block_type: str
    block_name: str
    block_uuid: UUID
    error_message: str

    @classmethod
    def from_error_message(cls, block: Block, error_message: str) -> Self:
        return cls(
            block_type=block.block_type,
            block_name=block.name,
            block_uuid=block.id,
            error_message=error_message,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BlockCodeGenerationResult:
    block: Block
    include: str = ""
    declaration: str = ""
    main_loop_body: str = ""
    errors: list[BlockCodeGenerationError] = field(
        default_factory=list[BlockCodeGenerationError],
    )

    def has_errors(self) -> bool:
        return len(self.errors) > 0


class BlockTypeImplementation(Protocol):
    def generate_code(
        self, program: Program, block: Block
    ) -> BlockCodeGenerationResult: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class BlockRegistration:
    block_type: BlockType
    implementation: BlockTypeImplementation


@dataclass(frozen=True, slots=True, kw_only=True)
class BlockTypesRegistry:
    block_types: dict[str, BlockRegistration] = field(default_factory=dict)

    def get_all_block_types(self) -> list[BlockType]:
        return [
            registration.block_type
            for registration in self.block_types.values()
        ]

    def get_block_type(self, block_type_name: str) -> BlockType:
        try:
            return self.block_types[block_type_name].block_type
        except KeyError:
            raise BlockTypeNotFoundError(block_type_name) from None

    def get_block_implementation(
        self, block_type_name: str
    ) -> BlockTypeImplementation:
        try:
            return self.block_types[block_type_name].implementation
        except KeyError:
            raise BlockTypeNotFoundError(block_type_name) from None

    def register(
        self,
        block_type: BlockType,
        implementation: BlockTypeImplementation,
    ) -> None:
        if block_type.name in self.block_types:
            err_msg = f"Block type already registered: {block_type.name}"
            raise ValueError(err_msg)

        self.block_types[block_type.name] = BlockRegistration(
            block_type=block_type,
            implementation=implementation,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CompilationArtifacts:
    asm_code: str
    hex_code: str


def port_configuration(name: str = "port") -> EnumConfiguration:
    return EnumConfiguration(
        name=name,
        choices=("A", "B", "C", "D"),
        default="A",
    )


def pin_configuration(
    name: str = "pin",
    min: int = 0,
    max: int = 7,
) -> IntegerConfiguration:
    return IntegerConfiguration(name=name, min=min, max=max, default=0)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProgramBuildResult:
    program: Program
    errors: list[BlockCodeGenerationError] = field(
        default_factory=list[BlockCodeGenerationError],
    )

    def has_errors(self) -> bool:
        return len(self.errors) > 0


@dataclass(frozen=True, slots=True, kw_only=True)
class DeviceInfo:
    name: str
    id: str
