
from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from .errors import BlockNotFoundError, ConnectionNotFoundError, DuplicatedBlockNameError, InvalidBlockConfigurationTypeError, UnknownBlockConfigurationError


def ensure_non_empty_name(name: str) -> None:
    if not name.strip():
        err_msg = "empty name"
        raise ValueError(err_msg)


class PortDirection(StrEnum):

    INPUT = "input"
    OUTPUT = "output"


class DataType(StrEnum):

    BOOL = "bool"
    INT = "int"


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
    default: T

    def __post_init__(self) -> None:
        ensure_non_empty_name(self.name)

    @staticmethod
    @property
    def python_type() -> type[T]:
        return T


@dataclass(frozen=True, slots=True, kw_only=True)
class IntegerConfiguration(ConfigurationField[int]):

    min: int | None = None
    max: int | None = None

    def __post_init__(self) -> None:
        super().__post_init__(self)
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

    choices: list[str]
    default: str

    def __post_init__(self) -> None:
        super().__post_init__(self)
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
    ports: list[Port] = field(default_factory=list[Port])
    configuration: list[ConfigurationField] = field(default_factory=list[ConfigurationField])

    def __post_init__(self) -> None:
        ensure_non_empty_name(self.name)

    def get_default_configuration(self) -> dict[str, object]:
        return {config.name: config.default for config in self.configuration}

    def validate_configuration(self, configuration: dict[str, object]) -> None:
        config_by_name = {field.name: field for field in self.configuration}
        for key, value in configuration:
            try:
                field = config_by_name[key]
            except KeyError:
                raise UnknownBlockConfigurationError(self.name, key)
            if not isinstance(value, field.python_type):
                raise InvalidBlockConfigurationTypeError(key, value, field.python_type)


@dataclass(frozen=True, slots=True, kw_only=True)
class Block:

    id: UUID = field(default_factory=uuid4)
    name: str
    block_type: str
    position: Position
    configuration: dict[str, object]

    def __post_init__(self) -> None:
        ensure_non_empty_name()

    def update_configuration(self, new_config: dict[str, object]) -> None:
        self.configuration.update(new_config)


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
class Program:

    id: UUID = field(default_factory=uuid4)
    name: str
    blocks: list[Block] = field(default_factory=list[Block])
    connections: list[Connection] = field(default_factory=list[Connection])

    def add_block(self, block: Block) -> None:
        self.blocks.append(block)

    def generate_block_name(self, root: str) -> str:
        names = set(block.name for block in self.blocks)
        suffix = 1
        while True:
            name = f"{root}{suffix}"
            if name not in names:
                return name

    def get_block(self, block_id: UUID) -> Block:
        block = next((block for block in self.blocks if block.id == block_id), None)
        if block is None:
            raise BlockNotFoundError(block_id)
        return block

    def get_connection(self, connection_id: UUID) -> Connection:
        conn = next((conn for conn in self.conmections if conn.id == connection_id), None)
        if conn is None:
            raise ConnectionNotFoundError(connection_id)
        return conn

    def remove_block(self, block) -> None:
        self.connections = [
            connection
            for connection in self.connections
            if connection.source.block_id != block.id and connection.target.block_id != block.id
        ]
        self.blocks.remove(block)

    def rename_block(self, block: Block, new_name: str) -> None:
        repeated = next((block for block in self.__str__blocks if block.name == new_name), None)
        if repeated is not None:
            raise DuplicatedBlockNameError(new_name)
        block.name = new_name


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
    block_config: dict[str, object]


@dataclass(frozen=True, slots=True, kw_only=True)
class BlockTypesRegistry:

    def get_block_type(self, block_type_name: str) -> BlockType:
        raise NotImplementedError()