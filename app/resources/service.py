from typing import Optional, Tuple

from cryptic import register_errors
from sqlalchemy import func

import resources.game_content as game_content
from app import m, wrapper
from models.bruteforce import Bruteforce
from models.miner import Miner
from models.service import Service
from resources.errors import service_exists, device_online, device_accessible, has_service_and_device
from resources.essentials import (
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
    service_cannot_be_used,
    service_not_supported,
    already_own_this_service,
    success_scheme,
    standard_scheme,
    cannot_toggle_directly,
    device_scheme,
    could_not_start_service,
    cannot_delete_enforced_service,
)
from vars import config

switch: dict = {  # this is just for tools, its a more smooth way of a "switch" statement
    "portscan": game_content.portscan
}


@m.user_endpoint(path=["public_info"], requires=standard_scheme)
@register_errors(service_exists(), device_online)
def public_info(data: dict, user: str, service: Service) -> dict:
    if service.running_port is None or not service.running:
        return service_not_found

    return service.public_data()


@m.user_endpoint(path=["use"], requires=None)
@register_errors(has_service_and_device, service_exists(), device_online, device_accessible)
def use(data: dict, user: str, service: Service) -> dict:
    if service.name not in switch:
        return service_cannot_be_used

    return switch[service.name](data, user)


@m.user_endpoint(path=["private_info"], requires=standard_scheme)
@register_errors(service_exists(), device_online, device_accessible)
def private_info(data: dict, user: str, service: Service) -> dict:
    return service.serialize


@m.user_endpoint(path=["toggle"], requires=standard_scheme)
@register_errors(service_exists(), device_online, device_accessible)
def toggle(data: dict, user: str, service: Service) -> dict:
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
@register_errors(service_exists(), device_online, device_accessible)
def delete_service(data: dict, user: str, service: Service) -> dict:
    if service.name == "ssh":
        return cannot_delete_enforced_service

    delete_one_service(service)

    return success_scheme


@m.user_endpoint(path=["list"], requires=device_scheme)
@register_errors(device_online, device_accessible)
def list_services(data: dict, user: str) -> dict:
    return {
        "services": [
            service.serialize for service in wrapper.session.query(Service).filter_by(device=data["device_uuid"]).all()
        ]
    }


@m.user_endpoint(path=["create"], requires=None)
@register_errors(device_online, device_accessible)
def create(data: dict, user: str) -> dict:
    device_uuid: str = data["device_uuid"]
    name: str = data["name"]

    if name not in config["services"]:
        return service_not_supported

    device_owner: str = get_device_owner(device_uuid)
    service_count: int = wrapper.session.query(func.count(Service.name)).filter_by(
        owner=device_owner, device=device_uuid, name=name
    ).scalar()
    if service_count != 0:
        return already_own_this_service

    return create_service(name, data, device_owner)


@m.user_endpoint(path=["part_owner"], requires=device_scheme)
@register_errors(device_online)
def part_owner(data: dict, user: str) -> dict:
    return {"ok": game_content.part_owner(data["device_uuid"], user)}


@m.user_endpoint(path=["list_part_owner"], requires={})
def list_part_owner(data: dict, user: str) -> dict:
    return {"services": [service.serialize for service in wrapper.session.query(Service).filter_by(part_owner=user)]}


@m.microservice_endpoint(path=["device_init"])
def device_init(data: dict, microservice: str) -> dict:
    create_service("ssh", data, data["user"])
    return success_scheme


@m.microservice_endpoint(path=["device_restart"])
def device_restart(data: dict, microservice: str) -> dict:
    service: Optional[Service] = wrapper.session.query(Service).filter_by(
        device=data["device_uuid"], name="ssh"
    ).first()
    if service is not None:
        if register_service(service.device, service.uuid, service.name, service.owner) == -1:
            return could_not_start_service
        service.running = True
        wrapper.session.commit()
    else:
        create_service("ssh", data, data["user"])

    return success_scheme


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


@m.microservice_endpoint(path=["delete_user"])
def delete_user(data: dict, microservice: str) -> dict:
    """
    Delete all devices of a user.

    :param data: The given data.
    :param microservice: The name of the requesting microservice
    :return: Success or not
    """
    user_uuid: str = data["user_uuid"]

    for service in wrapper.session.query(Service).filter_by(owner=user_uuid):

        # delete bruteforce if service is bruteforce
        bruteforce = wrapper.session.query(Bruteforce).filter_by(uuid=service.uuid).first()
        if bruteforce is not None:
            wrapper.session.delete(bruteforce)

        # delete miner if service is miner
        miner = wrapper.session.query(Miner).filter_by(uuid=service.uuid).first()
        if miner is not None:
            wrapper.session.delete(miner)

        # delete the service itself
        wrapper.session.delete(service)

    wrapper.session.commit()

    return success_scheme
