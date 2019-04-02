from typing import Optional, List

import cryptic
from sqlalchemy import func

import resources.game_content as game_content
from models.Service import Service
from objects import *
from objects import session
from schemes import *
from vars import config

switch: dict = {  # This is just for Tools
    "Hydra": game_content.bruteforce,
    "nmap": game_content.nmap
}

m: cryptic.MicroService = cryptic.MicroService(name = 'service')

def calculate_pos(waited_time: int) -> 'int':
    """
    :param waited_time: How long the user already penetrate the service
    :return: chance that this brute force attack is successful (return , 1)
    """
    return waited_time / config["CHANCE"]

@m.user_endpoint(path = ["public_info"])
def public_info(data: dict, user: str) -> dict:
    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()
    if service.running_port is None and (service.owner != user or service.part_owner != user):
        return unknown_service
    return service.public_data()

@m.user_endpoint(path = ["use"])
def use(data: dict, user: str) -> dict:
    if "device_uuid" not in data or "service_uuid" not in data:
        return invalid_request

    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()

    if service is None or (
            part_owner({"device_uuid": data["device_uuid"]}, user)["ok"] is False and service.owner != user):
        return unknown_service

    return switch[service.name](data, user)

@m.user_endpoint(path = ["private_info"])
def private_info(data: dict, user: str) -> dict:
    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()

    if service is None:
        return invalid_request

    if user != service.owner and user != service.part_owner:
        return permission_denied

    return service.serialize

@m.user_endpoint(path = ["turn_off_on"])
def turnoff_on(data: dict, user: str) -> dict:
    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()

    if service is None:
        return invalid_request

    if user != service.owner:
        return permission_denied

    service.running: bool = not service.running
    service.action = None
    service.target_service: str = ""
    service.target_device: str = ""

    session.commit()

    return {"ok": True}

@m.user_endpoint(path = ["delete"])
def delete_service(data: dict, user: str) -> dict:
    service: Optional[Service] = session.query(Service).filter(uuid=data["service_uuid"],
                                                               device=data["device_uuid"]).first()

    if service is None:
        return invalid_request

    if user != service.owner:
        return permission_denied

    session.delete(service)
    session.commit()

    return {"ok": True}

@m.user_endpoint(path = ["list"])
def list_services(data: dict, user: str) -> dict:
    services: List[Service] = session.query(Service).filter_by(owner=user,
                                                               device=data["device_uuid"]).all()

    return {
        "services": [e.serialize for e in services if e.owner == user]
    }

@m.user_endpoint(path = ["create"])
def create(data: dict, user: str) -> dict:
    owner: str = user
    name: str = data["name"]

    if name not in config["services"].keys():
        return service_is_not_supported

    if "device_uuid" not in data:
        return invalid_request

    data_return: dict = m.contact_microservice("device", ["exist"],{"device_uuid": data["device_uuid"]})

    if "exist" not in data_return or data_return["exist"] is False:
        return device_does_not_exist

    service_count: int = \
        (session.query(func.count(Service.name)).filter(Service.owner == owner,
                                                        Service.device == data["device_uuid"],
                                                        Service.name == name)).first()[0]

    if service_count != 0:
        return multiple_services

    service: Service = Service.create(owner, data["device_uuid"], name)

    return service.serialize

@m.user_endpoint(path = ["part_owner"])
def part_owner(data: dict, user: str) -> dict:
    services: List[Service] = session.query(Service).filter_by(device=data["device_uuid"]).all()

    for e in services:
        if e.part_owner == user and e.running_port is not None and config["services"][e.name][
            "allow_remote_access"] is True:
            return success_scheme

    return {"ok": False}


@m.microservice_endpoint(path = ["check_part_owner"])
def handle_microservice_requests(data: dict, microservice: str) -> dict:
    """ all this requests are trusted"""
    return part_owner(data, data["user_uuid"])
