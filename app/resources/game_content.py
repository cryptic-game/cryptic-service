from app import wrapper
from models.service import Service
from schemes import invalid_request
from vars import config
from typing import Tuple


def calculate_pos(waited_time: float) -> float:
    """
    :param waited_time: How long the user already penetrate the service
    :return: chance that this brute force attack is successful (return , 1)
    """
    return waited_time / config["CHANCE"]


def portscan(data: dict, user: str) -> dict:
    if "target_device" not in data:
        return invalid_request

    target_device: str = data["target_device"]
    if not isinstance(target_device, str):
        return invalid_request

    return {
        "services": [
            service.public_data()
            for service in wrapper.session.query(Service).filter_by(device=target_device).all()
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


def dict2tuple(data: dict) -> Tuple[float, float, float, float, float]:
    return data["cpu"], data["ram"], data["gpu"], data["disk"], data["network"]


def calculate_speed(
    edata: Tuple[float, float, float, float, float], rdata: Tuple[float, float, float, float, float]
) -> float:
    return min(sum(rdata) / sum(edata), 1)
