from typing import Optional, List
from models.Service import Service
from objects import db
from config import config
import random
import time
from python3_lib.cryptic import MicroService
from schemes import *

from sqlalchemy import func


def calculate_pos(waited_time: int) -> 'int':
    """
    :param waited_time: How long the user already penetrate the service
    :return: chance that this brute force attack is successful (return , 1)
    """
    return waited_time / config["CHANCE"]


def public_info(data: dict) -> dict:
    service: Optional[Service] = Service.query.filter_by(uuid=data["uuid"], device=data["device"]).first()
    return service


def hack(data: dict) -> dict:
    m.send_ms("device", {"device": data["device"]})

    """
    We need a function which waits for the response
    """

    if "target_service" not in data or "target_device" not in data:
        return invalid_request

    service: Optional[Service] = Service.query.filter_by(uuid=data["uuid"], device=["device"]).first()

    if service.target_device == data["target_device"] and service.target_service == data["target_service"]:
        target_service: Optional[Service] = Service.query.filter_by(uuid=data["target_service"],
                                                                    device=data["target_device"]).first()
        pen_time: int = time.time() - service.action

        print(calculate_pos(int(pen_time)))

        service.use(target_service=None, target_device=None)

        random_value = random.random() + 0.1

        if random_value < calculate_pos(int(pen_time)):
            target_service.part_owner = data["owner"]  # TODO
            db.session.commit()

            return {"ok": True, "access": True, "time": pen_time}
        else:
            return {"ok": True, "access": False, "time": pen_time}

    service.use(target_service=data["target_service"], target_device=data["target_device"])

    return success_scheme


def private_info(data: dict) -> dict:
    service: Optional[Service] = Service.query.filter_by(uuid=data["uuid_service"], device=data["uuid_device"]).first()

    if service is None:
        return invalid_request

    if data["owner"] != service.owner and data["owner"] != service.part_owner:  # TODO
        return permission_denied

    service.running: bool = not service.running
    db.session.commit()

    return service.serialize


def turnoff_on(data: dict) -> dict:
    service: Optional[Service] = Service.query.filter_by(uuid=data["uuid_service"], device=data["uuid_device"]).first()

    if service is None:
        return invalid_request

    if data["owner"] != service.owner and data["owner"] != service.part_owner:  # TODO
        return permission_denied

    service.running: bool = not service.running
    db.session.commit()

    return service.serialize


def delete_service(data: dict) -> dict:
    service: Optional[Service] = Service.query.filter_by(uuid=data["uuid_service"], device=data["uuid_device"]).first()

    if service is None:
        return invalid_request

    if data["owner"] != service.owner:  # TODO
        return permission_denied

    db.session.delete(service)
    db.session.commit()

    return {"ok": True}


def list_services(data: dict) -> dict:
    services: List[Service] = Service.query.filter_by(owner=data["owner"], device=data["uuid_device"]).all()  # TODO

    return {
        "services": [e.serialize for e in services]
    }


def create(data: dict) -> dict:
    owner: str = data["owner"]  # TODO
    name: str = data["name"]

    available_services: List[str] = ["SSH", "Telnet", "Hydra", "nmap"]

    if name not in available_services:
        return service_is_not_supported

    service_count: int = \
        (db.session.query(func.count(Service.name)).filter(Service.owner == owner,
                                                           Service.device == data["uuid_device"])).first()[0]

    if service_count != 0:
        return mutiple_services

    service: Service = Service.create(owner, data["uuid_device"], name, True)

    return service.serialize


def part_owner(data: dict) -> dict:
    services: List[Service] = Service.query.filter_by(device=data["uuid_device"]).all()

    for e in services:
        if e.part_owner == data["owner"]:  # TODO
            return success_scheme

    return {"ok": False}


def handle(endpoint: List[str], data: dict):
    """
    This function just forwards the data to the responsible function.
    :param endpoint:
    :param data:
    :return:
    """
    print(endpoint, data)
    # device_api_response: requests.models.Response = post(config["DEVICE_API"] + "public/" + str(device)).json() TODO

    if endpoint[0] == "public_info":
        return public_info(data)

    elif endpoint[0] == "hack":
        return hack(data)

    elif endpoint[0] == "private_info":
        return private_info(data)

    elif endpoint[0] == "turn":
        return turnoff_on(data)

    elif endpoint[0] == "delete":
        return delete_service(data)

    elif endpoint[0] == "list":
        return list_services(data)

    elif endpoint[0] == "create":
        return create(data)

    elif endpoint[0] == "part_owner":
        return part_owner(data)

    return {"error": 404, "message": "endpoint is unknown"}


def handle_mirce_service_requests(ms, data):
    """ all this requests are trusted"""
    pass


m = MicroService('service', handle, handle_mirce_service_requests, True)
