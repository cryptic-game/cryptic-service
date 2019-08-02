import random
import time

from app import m, wrapper
from models.bruteforce import Bruteforce
from models.service import Service
from resources.game_content import calculate_pos
from schemes import *


@m.user_endpoint(path=["bruteforce", "attack"], requires=attack_scheme)
def attack(data: dict, user: str):
    target_device: str = data["target_device"]
    target_service_uuid: str = data["target_service"]

    service: Bruteforce = wrapper.session.query(Bruteforce).filter_by(uuid=data["service_uuid"]).first()

    target_service: Service = wrapper.session.query(Service).filter_by(
        uuid=target_service_uuid, device=target_device
    ).first()
    if service is None or target_service is None:
        return service_not_found
    if not target_service.running:
        return service_not_running

    service.target_service: str = target_service_uuid
    service.target_device: str = target_device
    service.started: int = int(time.time())
    wrapper.session.commit()

    return success_scheme


@m.user_endpoint(path=["bruteforce", "status"], requires=standard_scheme)
def status(data: dict, user: str):
    service: Bruteforce = wrapper.session.query(Bruteforce).filter_by(uuid=data["service_uuid"]).first()

    if service is None:
        return service_not_found

    if service.target_device is None or service.target_service is None or service.started is None:
        return attack_not_running

    return {**service.serialize, "pen_time": time.time() - service.started}


@m.user_endpoint(path=["bruteforce", "stop"], requires=standard_scheme)
def stop(data: dict, user: str):
    service: Bruteforce = wrapper.session.query(Bruteforce).filter_by(uuid=data["service_uuid"]).first()

    if service is None:
        return service_not_found

    if service.target_device is None or service.target_service is None or service.started is None:
        return attack_not_running

    target_device: str = service.target_device

    target_service: Service = wrapper.session.query(Service).filter_by(
        uuid=service.target_service, device=target_device
    ).first()
    if target_service is None:
        return service_not_found

    pen_time: float = (time.time() - service.started) * service.speed

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
