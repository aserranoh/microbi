from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .domain.blocks.builtin import digital_input, digital_output, int8_constant
from .domain.models import BlockTypesRegistry
from .routers import block_types, programs


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.block_types_registry = BlockTypesRegistry()
    digital_input.init(app.state.block_types_registry)
    digital_output.init(app.state.block_types_registry)
    int8_constant.init(app.state.block_types_registry)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(block_types.router)
app.include_router(programs.router)
