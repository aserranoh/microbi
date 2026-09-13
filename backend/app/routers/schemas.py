from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models import (
    AddBlockRequest,
    ConnectBlocksRequest,
    CreateProgramRequest,
    DataType,
    FieldType,
    PortDirection,
    ProgramArtifact,
    UpdateBlockRequest,
    UpdateProgramRequest,
)


class CreateProgramRequestIn(BaseModel):
    name: str = Field(min_length=1)
    mcu: str = Field(min_length=1)

    def domain_model(self) -> CreateProgramRequest:
        return CreateProgramRequest(**self.model_dump())


class UpdateProgramRequestIn(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    mcu: str | None = Field(default=None, min_length=1)

    def domain_model(self, program_id: UUID) -> UpdateProgramRequest:
        return UpdateProgramRequest(
            **self.model_dump(exclude_unset=True),
            id=program_id,
        )


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
    block_name: str | None = Field(
        default=None,
        pattern=r"^[_a-zA-Z][_a-zA-Z0-9]*$",
    )
    block_position: PositionIn | None = None
    block_config: dict[str, object] | None = None

    def domain_model(
        self,
        program_id: UUID,
        block_id: UUID,
    ) -> UpdateBlockRequest:
        return UpdateBlockRequest(
            **self.model_dump(exclude_unset=True),
            program_id=program_id,
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


class PositionResponse(BaseModel):
    x: float
    y: float


class BlockResponse(BaseModel):
    id: UUID
    name: str
    block_type: str
    position: PositionResponse
    configuration: dict[str, object]


class PortReferenceResponse(BaseModel):
    block_id: UUID
    port_name: str


class ConnectionResponse(BaseModel):
    id: UUID
    source: PortReferenceResponse
    target: PortReferenceResponse


class ProgramResponse(BaseModel):
    id: UUID
    name: str
    blocks: list[BlockResponse]
    connections: list[ConnectionResponse]
    mcu: str
    revision: int
    modified_at: datetime
    artifacts: list[ProgramArtifact]


class IntegerConfigurationResponse(BaseModel):
    name: str
    type: Literal[FieldType.INTEGER]
    default: int
    min: int | None = None
    max: int | None = None


class EnumConfigurationResponse(BaseModel):
    name: str
    type: Literal[FieldType.ENUM]
    default: str
    choices: list[str]


ConfigurationResponse = Annotated[
    IntegerConfigurationResponse | EnumConfigurationResponse,
    Field(discriminator="type"),
]


class PortResponse(BaseModel):
    name: str
    direction: PortDirection
    data_type: DataType


class BlockTypeResponse(BaseModel):
    name: str
    description: str
    ports: list[PortResponse]
    configuration: list[ConfigurationResponse]
