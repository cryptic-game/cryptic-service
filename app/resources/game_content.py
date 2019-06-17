import random
import time
from typing import Optional, List
from math import sqrt, exp
from app import wrapper
from models.service import Service
from schemes import *
from vars import config
from models.bruteforce import Bruteforce


def calculate_pos(waited_time: int) -> int:
    """
    :param waited_time: How long the user already penetrate the service
    :return: chance that this brute force attack is successful (return , 1)
    """
    return waited_time / config["CHANCE"]


def bruteforce(data: dict, user: str) -> dict:
    if "target_device" not in data or "target_service" not in data:
        return invalid_request

    service: Optional[Bruteforce] = wrapper.session.query(Bruteforce).filter_by(uuid=data["service_uuid"])
    target_service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=data["target_service"],
                                                                                 device=data["target_device"]).first()

    if target_service is None or target_service.running is False or target_service.running_port is None or \
            config["services"][target_service.name]["allow_remote_access"] is False:
        return unknown_service

    if service.target_device == data["target_device"] and service.target_service == data["target_service"]:
        pen_time: float = time.time() - service.action

        service.use(data)

        random_value: float = random.random() + 0.1

        target_device: str = service.target_device

        service.target_device = None
        service.target_service = None
        service.action = None
        wrapper.session.commit()

        if random_value < calculate_pos(int(pen_time)):
            target_service.part_owner: str = user
            wrapper.session.commit()

            return {"ok": True, "access": True, "time": pen_time, "target_device": target_device}
        else:
            return {"ok": True, "access": False, "time": pen_time, "target_device": target_device}
    else:
        service.use(data)

        return success_scheme


def portscan(data: dict, user: str) -> dict:
    if "target_device" not in data:
        return unknown_service

    services: List[Service] = wrapper.session.query(Service).filter_by(device=data["target_device"]).all()

    return_data: list = []

    for service in services:
        if service.running_port is not None:
            return_data.append(service.public_data())

    return {"services": return_data}


def part_owner(device: str, user: str) -> bool:
    services: List[Service] = wrapper.session.query(Service).filter_by(device=device).all()

    for e in services:
        if e.part_owner == user and e.running_port is not None and \
                config["services"][e.name]["allow_remote_access"] is True:
            return True

    return False
