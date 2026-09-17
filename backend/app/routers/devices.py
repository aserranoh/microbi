from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.dependencies import get_devices_repository
from app.domain import use_cases
from app.domain.adapters import DevicesRepository
from app.domain.models import DeviceInfo

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/{device_id}")
async def get_device_info(
    device_id: Annotated[
        str,
        Path(pattern=r"^[0-9a-zA-Z]{4}:[0-9a-zA-Z]{4}$"),
    ],
    adapter: Annotated[DevicesRepository, Depends(get_devices_repository)],
) -> DeviceInfo:
    return await use_cases.get_device_info(device_id, adapter)
