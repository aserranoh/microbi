
from typing import Protocol
from uuid import UUID

from .models import Program


class ProgramsRepositoryPort(Protocol):

    def get_all(self) -> list[Program]:
        ...

    def get_by_name(self, program_name: str) -> Program | None:
        ...

    def get_by_id(self, program_id: UUID) -> Program:
        ...

    def create(self, program_name: str) -> Program:
        ...

    def delete(self, program: Program) -> None:
        ...

    def update(self, program: Program) -> None:
        ...