from schemes import *
from vars import config
from typing import Optional, List
from objects import session
import random
import time
from models.Service import Service


def calculate_pos(waited_time: int) -> 'int':
    """
    :param waited_time: How long the user already penetrate the service
    :return: chance that this brute force attack is successful (return , 1)
    """
    return waited_time / config["CHANCE"]


def bruteforce(data: dict, user: str) -> dict:
    if "target_device" not in data or "target_service" not in data:
        return invalid_request

    service: Optional[Service] = session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                  device=data["device_uuid"]).first()
    target_service: Optional[Service] = session.query(Service).filter_by(uuid=data["target_service"],
                                                                         device=data["target_device"]).first()

    if target_service is None or target_service.running is False or target_service.running_port is None or \
            config["services"][target_service.name]["allow_remote_access"] is False:
        return unknown_service

    if service.target_device == data["target_device"] and service.target_service == data["target_service"]:

        pen_time: float = time.time() - service.action

        service.use(data)

        random_value: float = random.random() + 0.1

        if random_value < calculate_pos(int(pen_time)):
            target_service.part_owner: str = user
            session.commit()

            return {"ok": True, "access": True, "time": pen_time}
        else:
            return {"ok": True, "access": False, "time": pen_time}

    else:
        service.use(data)

        return success_scheme


def nmap(data: dict, user: str) -> dict:
    if "target_service" not in data and "target_device" not in data:
        return unknown_service

    services: List[Service] = session.query(Service).filter_by(device=data["target_device"]).all()

    return_data: list = []

    for service in services:
        if service.running_port is not None:
            return_data.append(service.public_data())

    return {"services": return_data}
