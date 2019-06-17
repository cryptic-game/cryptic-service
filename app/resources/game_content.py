import random
import time

from app import wrapper
from models.bruteforce import Bruteforce
from models.service import Service
from schemes import *
from vars import config


def calculate_pos(waited_time: float) -> float:
    """
    :param waited_time: How long the user already penetrate the service
    :return: chance that this brute force attack is successful (return , 1)
    """
    return waited_time / config["CHANCE"]


def bruteforce(data: dict, user: str) -> dict:
    if "target_device" not in data or "target_service" not in data:
        return invalid_request

    target_device: str = data["target_device"]
    target_service_uuid: str = data["target_service"]
    if not isinstance(target_device, str) or not isinstance(target_service_uuid, str):
        return invalid_request

    service: Bruteforce = wrapper.session.query(Bruteforce).filter_by(uuid=data["service_uuid"]).first()
    target_service: Service = wrapper.session.query(Service).filter_by(uuid=target_service_uuid,
                                                                       device=target_device).first()

    if target_service is None or target_service.running is False or target_service.running_port is None \
            or not config["services"][target_service.name]["allow_remote_access"]:
        return unknown_service

    if service.target_device == target_device and service.target_service == target_service.uuid:
        pen_time: float = time.time() - service.started

        random_value: float = random.random() + 0.1

        service.target_device = None
        service.target_service = None
        service.started = None
        wrapper.session.commit()

        access: bool = False
        if random_value < calculate_pos(pen_time):
            target_service.part_owner: str = user
            wrapper.session.commit()
            access: bool = True

        return {"ok": True, "access": access, "time": pen_time, "target_device": target_device}
    else:
        service.use(target_service.uuid, target_device)

        return success_scheme


def portscan(data: dict, user: str) -> dict:
    if "target_device" not in data:
        return invalid_request

    target_device: str = data["target_device"]
    if not isinstance(target_device, str):
        return invalid_request

    return {
        "services": [
            service.public_data() for service in
            wrapper.session.query(Service).filter_by(device=target_device).all()
            if service.running_port is not None and service.running
        ]
    }


def part_owner(device: str, user: str) -> bool:
    for service in wrapper.session.query(Service).filter_by(device=device).all():
        if service.part_owner != user:
            continue
        if service.running_port is not None and config["services"][service.name]["allow_remote_access"]:
            return True
    return False
