from typing import Optional, Callable

from cryptic import MicroserviceException

from app import wrapper
from models.service import Service
from resources.essentials import exists_device, controls_device, check_device_online
from schemes import service_not_found, device_not_found, permission_denied, device_not_online, invalid_request


def has_service_and_device(data: dict, user: str):
    if not (isinstance(data.get("service_uuid"), str) and isinstance(data.get("device_uuid"), str)):
        raise MicroserviceException(invalid_request)

    return ()


def service_exists(name: str = None, device_required: bool = True) -> Callable[[dict, str], Service]:
    def deco(data: dict, user: str) -> Service:
        if device_required:
            service: Optional[Service] = wrapper.session.query(Service).filter_by(
                uuid=data["service_uuid"], device=data["device_uuid"]
            ).first()
        else:
            service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=data["service_uuid"]).first()

        if service is None:
            raise MicroserviceException(service_not_found)

        if name is not None and service.name != name:
            raise MicroserviceException(service_not_found)

        return service

    return deco


def device_online(data: dict, user: str, service: Service = None) -> Service:
    device_uuid = service.device if service is not None else data["device_uuid"]

    if not exists_device(device_uuid):
        raise MicroserviceException(device_not_found)
    if not check_device_online(device_uuid):
        raise MicroserviceException(device_not_online)

    return service if service is not None else ()


def device_accessible(data: dict, user: str, service: Service = None) -> Service:
    device_uuid = service.device if service is not None else data["device_uuid"]

    if not controls_device(device_uuid, user):
        raise MicroserviceException(permission_denied)

    return service if service is not None else ()
