from typing import Optional, List

from app import m, wrapper
from sqlalchemy import func
import resources.game_content as game_content
from models.Service import Service
from schemes import *
from vars import config

switch: dict = {  # This is just for Tools
    "brute4ce": game_content.bruteforce,
    "portscan": game_content.portscan
}


@m.user_endpoint(path=["public_info"])
def public_info(data: dict, user: str) -> dict:
    if "service_uuid" not in data or "device_uuid" not in data:
        return invalid_request

    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                          device=data["device_uuid"]).first()
    if service is None or service.running_port is None:
        return unknown_service
    return service.public_data()


@m.user_endpoint(path=["use"])
def use(data: dict, user: str) -> dict:
    if "device_uuid" not in data or "service_uuid" not in data:
        return invalid_request

    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                          device=data["device_uuid"]).first()

    if service is None or (
            not game_content.part_owner(data["device_uuid"], user) and service.owner != user):
        return unknown_service

    return switch[service.name](data, user)


@m.user_endpoint(path=["private_info"])
def private_info(data: dict, user: str) -> dict:
    if "service_uuid" not in data or "device_uuid" not in data:
        return invalid_request

    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                          device=data["device_uuid"]).first()

    if service is None:
        return invalid_request

    if user != service.owner and user != service.part_owner:
        return permission_denied

    return service.serialize


@m.user_endpoint(path=["turn_off_on"])
def turnoff_on(data: dict, user: str) -> dict:
    if "service_uuid" not in data or "device_uuid" not in data:
        return invalid_request

    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                          device=data["device_uuid"]).first()

    if service is None:
        return invalid_request

    if user != service.owner:
        return permission_denied

    service.running: bool = not service.running
    service.action = None
    service.target_service: str = ""
    service.target_device: str = ""

    wrapper.session.commit()

    return {"ok": True}


@m.user_endpoint(path=["delete"])
def delete_service(data: dict, user: str) -> dict:
    if "service_uuid" not in data or "device_uuid" not in data:
        return invalid_request

    service: Optional[Service] = wrapper.session.query(Service).filter(uuid=data["service_uuid"],
                                                                       device=data["device_uuid"]).first()

    if service is None:
        return invalid_request

    data_owner: dict = m.contact_microservice("device", ["owner"], {"device_uuid": data["device_uuid"]})

    if user != data_owner["owner"]:
        return permission_denied

    wrapper.session.delete(service)
    wrapper.session.commit()

    return {"ok": True}


@m.user_endpoint(path=["list"])
def list_services(data: dict, user: str) -> dict:
    if "device_uuid" not in data:
        return invalid_request

    data_return: dict = m.contact_microservice("device", ["owner"], {"device_uuid": data["device_uuid"]})

    if "owner" in data_return:
        if game_content.part_owner(data["device_uuid"], user) or user == data_return["owner"]:
            services: List[Service] = wrapper.session.query(Service).filter_by(
                device=data["device_uuid"]).all()
        else:
            return permission_denied
    else:
        return device_does_not_exist

    return {
        "services": [e.serialize for e in services]
    }


@m.user_endpoint(path=["create"])
def create(data: dict, user: str) -> dict:
    owner: str = user
    name: str = data["name"]

    if name not in config["services"].keys():
        return service_is_not_supported

    if "device_uuid" not in data:
        return invalid_request

    data_return: dict = m.contact_microservice("device", ["exist"], {"device_uuid": data["device_uuid"]})

    if "exist" not in data_return or data_return["exist"] is False:
        return device_does_not_exist

    data_owner: dict = m.contact_microservice("device", ["owner"], {"device_uuid": data["device_uuid"]})

    if data_owner["owner"] != user and not game_content.part_owner(data["device_uuid"], user):
        return permission_denied

    service_count: int = \
        (wrapper.session.query(func.count(Service.name)).filter(Service.owner == owner,
                                                                Service.device == data["device_uuid"],
                                                                Service.name == name)).first()[0]
    if service_count != 0:
        return multiple_services

    service: Service = Service.create(owner, data["device_uuid"], name)

    return service.serialize


@m.user_endpoint(path=["part_owner"])
def part_owner(data: dict, user: str) -> dict:
    if "device_uuid" not in data:
        return invalid_request

    return {"ok": game_content.part_owner(data["device_uuid"], user)}


@m.microservice_endpoint(path=["check_part_owner"])
def handle_microservice_requests(data: dict, microservice: str) -> dict:
    """ all this requests are trusted"""
    return part_owner(data, data["user_uuid"])
