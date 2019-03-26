from typing import Optional, List
from models.Service import Service
from config import config
import random
import time
import cryptic
from schemes import *
from objects import session
from uuid import uuid4
from sqlalchemy import func
from objects import *
from vars import config


#

def calculate_pos(waited_time: int) -> 'int':
    """
    :param waited_time: How long the user already penetrate the service
    :return: chance that this brute force attack is successful (return , 1)
    """
    return waited_time / config["CHANCE"]


def public_info(data: dict, user: str) -> dict:
    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],


                                                                  device=data["device_uuid"]).first()
    return service.serialize  # TODO


def hack(data: dict, user: str) -> dict:
    if "target_device" not in data:
        return invalid_request

    # data_return: dict = m.wait_for_response("device", {"endpoint": "exists", "device_uuid": data["target_device"]})
    data_return: dict = {"exist": True}
    if data_return["exist"] is False:
        return device_does_not_exsist

    if "target_service" not in data:
        return invalid_request

    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()

    if service.target_device == data["target_device"] and service.target_service == data["target_service"]:
        target_service: Optional[Service] = session.query(Service).filter_by(uuid=data["target_service"],
                                                                             device=data["target_device"]).first()
        pen_time: int = time.time() - service.action

        service.use(target_service=None, target_device=None)

        random_value: float = random.random() + 0.1

        if random_value < calculate_pos(int(pen_time)):
            target_service.part_owner: str = user
            session.commit()

            return {"ok": True, "access": True, "time": pen_time}
        else:
            return {"ok": True, "access": False, "time": pen_time}

    service.use(target_service=data["target_service"], target_device=data["target_device"])

    return success_scheme


def private_info(data: dict, user: str) -> dict:
    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()

    if service is None:
        return invalid_request

    if user != service.owner and user != service.part_owner:
        return permission_denied

    service.running: bool = not service.running
    session.commit()

    return service.serialize


def turnoff_on(data: dict, user: str) -> dict:
    session: Session = Session()

    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()

    if service is None:
        return invalid_request

    if user != service.owner and user != service.part_owner:
        return permission_denied

    service.running: bool = not service.running

    return service.serialize


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
        "services": [e.serialize for e in services]
    }


def create(data: dict, user: str) -> dict:
    owner: str = user
    name: str = data["name"]

    available_services: List[str] = ["SSH", "Telnet", "Hydra", "nmap"]

    if name not in available_services:
        return service_is_not_supported

    service_count: int = \
        (session.query(func.count(Service.name)).filter(Service.owner == owner,
                                                        Service.device == data["device_uuid"])).first()[0]

    if service_count != 0:
        return multiple_services

    service: Service = Service.create(owner, data["device_uuid"], name, True)

    return service.serialize


def part_owner(data: dict, user: str) -> dict:
    services: List[Service] = session.query(Service).filter_by(device=data["device_uuid"]).all()

    for e in services:
        if e.part_owner == user:
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
        return {"error":"specify an endpoint"}

    if endpoint[0] == "public_info":
        return public_info(data, user)

    elif endpoint[0] == "bruteforce":
        return hack(data, user)

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

    return unknown_endpoint


def handle_mircoservice_requests(data):
    """ all this requests are trusted"""
    if data["endpoint"] == "check_part_owner":
        return part_owner(data, data["user_uuid"])

    return unknown_endpoint
