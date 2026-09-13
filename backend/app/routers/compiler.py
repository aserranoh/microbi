from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_avr_gcc_compiler
from app.domain.adapters import AvrGccCompiler

router = APIRouter(prefix="/compiler", tags=["compiler"])


@router.get("/mcus/")
async def get_mcus(
    compiler: Annotated[AvrGccCompiler, Depends(get_avr_gcc_compiler)],
) -> list[str]:
    return compiler.get_mcus()
