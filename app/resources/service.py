from typing import Optional, List
from models.Service import Service
import cryptic
from schemes import *
from sqlalchemy import func
from objects import *
from vars import config
from objects import session
from uuid import uuid4
import resources.game_content as game_content

switch: dict = {  # This is just for Tools
    "Hydra": game_content.bruteforce,
    "nmap": game_content.nmap
}


def calculate_pos(waited_time: int) -> 'int':
    """
    :param waited_time: How long the user already penetrate the service
    :return: chance that this brute force attack is successful (return , 1)
    """
    return waited_time / config["CHANCE"]


def public_info(data: dict, user: str) -> dict:
    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()
    if service.running_port is None and (service.owner != user or service.part_owner != user):
        return unknown_service
    return service.public_data()


def use(data: dict, user: str) -> dict:
    if "device_uuid" not in data or "service_uuid" not in data:
        return invalid_request

    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()

    if service is None or (
            part_owner({"device_uuid": data["device_uuid"]}, user)["ok"] is False and service.owner != user):
        return unknown_service

    return switch[service.name](data, user)


def private_info(data: dict, user: str) -> dict:
    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()

    if service is None:
        return invalid_request

    if user != service.owner and user != service.part_owner:
        return permission_denied

    return service.serialize


def turnoff_on(data: dict, user: str) -> dict:

    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()

    if service is None:
        return invalid_request

    if user != service.owner:
        return permission_denied

    service.running: bool = not service.running
    service.action = None
    service.target_service : str = ""
    service.target_device : str = ""

    session.commit()

    return {"ok":True}


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


def list_services(data: dict, user: str) -> dict:
    services: List[Service] = session.query(Service).filter_by(owner=user,
                                                               device=data["device_uuid"]).all()

    return {
        "services": [e.serialize for e in services if e.owner == user]
    }


def create(data: dict, user: str) -> dict:
    owner: str = user
    name: str = data["name"]

    if name not in config["services"].keys():
        return service_is_not_supported

    if "device_uuid" not in  data:
        return invalid_request

    data_return: dict = m.wait_for_response("device", {"endpoint": "exists", "device_uuid": data["device_uuid"]})


    if "exist" not in data_return or data_return["exist"] is False:
        return device_does_not_exsist

    service_count: int = \
        (session.query(func.count(Service.name)).filter(Service.owner == owner,
                                                        Service.device == data["device_uuid"],
                                                        Service.name == name)).first()[0]

    if service_count != 0:
        return multiple_services

    service: Service = Service.create(owner, data["device_uuid"], name, True)

    return service.serialize


def part_owner(data: dict, user: str) -> dict:
    services: List[Service] = session.query(Service).filter_by(device=data["device_uuid"]).all()

    for e in services:
        if e.part_owner == user and e.running_port is not None and config["services"][e.name][
            "allow_remote_access"] is True:
            return success_scheme

    return {"ok": False}


def handle(endpoint: List[str], data: dict, user: str) -> dict:
    """
    This function just forwards the data to the responsible function.
    :param endpoint:
    :param data:
    :return:
    """
    print(endpoint, data)
    # device_api_response: requests.models.Response = post(config["DEVICE_API"] + "public/" + str(device)).json()
    if len(endpoint) == 0:
        return {"error": "specify an endpoint"}

    if endpoint[0] == "public_info":
        return public_info(data, user)

    elif endpoint[0] == "private_info":
        return private_info(data, user)

    elif endpoint[0] == "turn":
        return turnoff_on(data, user)

    elif endpoint[0] == "delete":
        return delete_service(data, user)

    elif endpoint[0] == "list":
        return list_services(data, user)

    elif endpoint[0] == "create":
        return create(data, user)

    elif endpoint[0] == "part_owner":
        return part_owner(data, user)

    elif endpoint[0] == "use":
        return use(data, user)

    return unknown_endpoint


def handle_mircoservice_requests(data: dict) -> dict:
    """ all this requests are trusted"""
    if data["endpoint"] == "check_part_owner":
        return part_owner(data, data["user_uuid"])

    return unknown_endpoint


m: cryptic.MicroService = cryptic.MicroService('service', handle, handle_mircoservice_requests)
