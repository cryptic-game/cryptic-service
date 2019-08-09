import random
import time

from app import m, wrapper
from models.bruteforce import Bruteforce
from models.service import Service
from resources.game_content import calculate_pos
from schemes import (
    attack_scheme,
    service_not_found,
    service_not_running,
    success_scheme,
    attack_not_running,
    standard_scheme,
)


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

    service.target_service = target_service_uuid
    service.target_device = target_device
    service.started = int(time.time())
    service.progress = 0
    wrapper.session.commit()

    return success_scheme


@m.user_endpoint(path=["bruteforce", "status"], requires=standard_scheme)
def status(data: dict, user: str):
    bruteforce: Bruteforce = wrapper.session.query(Bruteforce).get(data["service_uuid"])

    if bruteforce is None:
        return service_not_found

    if bruteforce.target_device is None or bruteforce.target_service is None or bruteforce.started is None:
        return attack_not_running

    service: Service = wrapper.session.query(Service).get(bruteforce.uuid)
    bruteforce.update_progress(service.speed)

    return {**bruteforce.serialize, "progress": bruteforce.progress}


@m.user_endpoint(path=["bruteforce", "stop"], requires=standard_scheme)
def stop(data: dict, user: str):
    bruteforce: Bruteforce = wrapper.session.query(Bruteforce).get(data["service_uuid"])

    if bruteforce is None:
        return service_not_found

    if bruteforce.target_device is None or bruteforce.target_service is None or bruteforce.started is None:
        return attack_not_running

    target_device: str = bruteforce.target_device

    target_service: Service = wrapper.session.query(Service).filter_by(
        uuid=bruteforce.target_service, device=target_device
    ).first()
    if target_service is None:
        return service_not_found

    service: Service = wrapper.session.query(Service).get(bruteforce.uuid)
    bruteforce.update_progress(service.speed)

    progress: float = bruteforce.progress

    random_value: float = random.random() + 0.1

    bruteforce.target_device = None
    bruteforce.target_service = None
    bruteforce.started = None
    bruteforce.progress = 0
    wrapper.session.commit()

    access: bool = False
    if random_value < calculate_pos(progress):
        target_service.part_owner = user
        wrapper.session.commit()
        access: bool = True

    return {"ok": True, "access": access, "time": progress, "target_device": target_device}
