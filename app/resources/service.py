from typing import Optional, Tuple

from sqlalchemy import func

import resources.game_content as game_content
from app import m, wrapper
from models.bruteforce import Bruteforce
from models.service import Service
from resources.essentials import (
    exists_device,
    controls_device,
    create_service,
    stop_services,
    delete_services,
    delete_one_service,
    stop_service,
    register_service,
    get_device_owner,
)
from schemes import (
    service_not_found,
    device_not_found,
    permission_denied,
    unknown_service,
    invalid_request,
    service_cannot_be_used,
    service_not_supported,
    already_own_this_service,
    success_scheme,
    standard_scheme,
    cannot_toggle_directly,
    device_scheme,
    could_not_start_service,
)
from vars import config

switch: dict = {  # this is just for tools, its a more smooth way of a "switch" statement
    "portscan": game_content.portscan
}


@m.user_endpoint(path=["public_info"], requires=standard_scheme)
def public_info(data: dict, user: str) -> dict:
    service: Optional[Service] = wrapper.session.query(Service).filter_by(
        uuid=data["service_uuid"], device=data["device_uuid"]
    ).first()
    if service is None or service.running_port is None or not service.running:
        return unknown_service
    return service.public_data()


@m.user_endpoint(path=["use"], requires=None)
def use(data: dict, user: str) -> dict:
    if "device_uuid" not in data or "service_uuid" not in data:
        return invalid_request

    device_uuid: str = data["device_uuid"]
    service_uuid: str = data["service_uuid"]
    if not isinstance(device_uuid, str) or not isinstance(service_uuid, str):
        return invalid_request

    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=service_uuid, device=device_uuid).first()

    if service is None or (service.owner != user and not game_content.part_owner(device_uuid, user)):
        return unknown_service

    if service.name not in switch:
        return service_cannot_be_used

    return switch[service.name](data, user)


@m.user_endpoint(path=["private_info"], requires=standard_scheme)
def private_info(data: dict, user: str) -> dict:
    service: Optional[Service] = wrapper.session.query(Service).filter_by(
        uuid=data["service_uuid"], device=data["device_uuid"]
    ).first()

    if service is None:
        return unknown_service

    if not service.check_access(user):
        return permission_denied

    return service.serialize


@m.user_endpoint(path=["toggle"], requires=standard_scheme)
def toggle(data: dict, user: str) -> dict:
    service: Optional[Service] = wrapper.session.query(Service).filter_by(
        uuid=data["service_uuid"], device=data["device_uuid"]
    ).first()

    if service is None:
        return service_not_found

    if user != service.owner:
        return permission_denied

    if not config["services"][service.name]["toggleable"]:
        return cannot_toggle_directly

    if service.running:
        stop_service(service.device, service.uuid, service.owner)
    else:
        if register_service(service.device, service.uuid, service.name, service.owner) == -1:
            return could_not_start_service

    service.running = not service.running
    wrapper.session.commit()

    return service.serialize


@m.user_endpoint(path=["delete"], requires=standard_scheme)
def delete_service(data: dict, user: str) -> dict:
    device_uuid: str = data["device_uuid"]
    service_uuid: str = data["service_uuid"]
    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=service_uuid, device=device_uuid).first()

    if service is None:
        return service_not_found

    if not controls_device(device_uuid, user):
        return permission_denied

    delete_one_service(service)

    return success_scheme


@m.user_endpoint(path=["list"], requires=device_scheme)
def list_services(data: dict, user: str) -> dict:
    if not exists_device(data["device_uuid"]):
        return device_not_found
    if not controls_device(data["device_uuid"], user):
        return permission_denied

    return {
        "services": [
            service.serialize for service in wrapper.session.query(Service).filter_by(device=data["device_uuid"]).all()
        ]
    }


@m.user_endpoint(path=["create"], requires=None)
def create(data: dict, user: str) -> dict:
    if "device_uuid" not in data or "name" not in data:
        return invalid_request

    device_uuid: str = data["device_uuid"]
    name: str = data["name"]

    if not isinstance(device_uuid, str) or not isinstance(name, str):
        return invalid_request

    if name not in config["services"]:
        return service_not_supported

    if not exists_device(device_uuid):
        return device_not_found

    if not controls_device(device_uuid, user):
        return permission_denied

    service_count: int = wrapper.session.query(func.count(Service.name)).filter_by(
        owner=user, device=device_uuid, name=name
    ).scalar()
    if service_count != 0:
        return already_own_this_service

    device_owner: str = get_device_owner(device_uuid)
    return create_service(name, data, device_owner)


@m.user_endpoint(path=["part_owner"], requires=device_scheme)
def part_owner(data: dict, user: str) -> dict:
    return {"ok": game_content.part_owner(data["device_uuid"], user)}


@m.microservice_endpoint(path=["check_part_owner"])
def check_part_owner(data: dict, microservice: str) -> dict:
    # all these requests are trusted
    return {"ok": game_content.part_owner(data["device_uuid"], data["user_uuid"])}


@m.microservice_endpoint(path=["hardware", "scale"])
def hardware_scale(data: dict, microservice: str) -> dict:
    service: Service = wrapper.session.query(Service).filter_by(uuid=data["service_uuid"]).first()

    given_per: Tuple[float, float, float, float, float] = game_content.dict2tuple(data)

    expected_per: Tuple[float, float, float, float, float] = game_content.dict2tuple(
        config["services"][service.name]["needs"]
    )

    if service.name == "bruteforce":
        bruteforce: Bruteforce = wrapper.session.query(Bruteforce).get(service.uuid)
        bruteforce.update_progress(service.speed)
    service.speed = config["services"][service.name]["speedm"](expected_per, given_per)

    wrapper.session.commit()

    return success_scheme


@m.microservice_endpoint(path=["hardware", "stop"])
def hardware_stop(data: dict, microservice: str) -> dict:
    stop_services(data["device_uuid"])
    return success_scheme


@m.microservice_endpoint(path=["hardware", "delete"])
def hardware_delete(data: dict, microservice: str) -> dict:
    delete_services(data["device_uuid"])
    return success_scheme
