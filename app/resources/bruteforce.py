import random
import time

from cryptic import register_errors

from app import m, wrapper
from models.bruteforce import Bruteforce
from models.service import Service
from resources.errors import service_exists, device_online, device_accessible
from resources.essentials import register_service, stop_service
from resources.game_content import calculate_pos
from schemes import (
    attack_scheme,
    service_not_found,
    service_not_running,
    success_scheme,
    attack_not_running,
    standard_scheme,
    attack_already_running,
    could_not_start_service,
)


@m.user_endpoint(path=["bruteforce", "attack"], requires=attack_scheme)
@register_errors(service_exists("bruteforce"), device_online, device_accessible)
def attack(data: dict, user: str, service: Service):
    if service.running:
        return attack_already_running

    target_device: str = data["target_device"]
    target_service_uuid: str = data["target_service"]

    target_service: Service = wrapper.session.query(Service).filter_by(
        uuid=target_service_uuid, device=target_device
    ).first()
    if target_service is None:
        return service_not_found
    if not target_service.running:
        return service_not_running

    speed: float = register_service(service.device, service.uuid, service.name, service.owner)
    if speed == -1:
        return could_not_start_service

    bruteforce: Bruteforce = wrapper.session.query(Bruteforce).get(service.uuid)
    bruteforce.target_service = target_service_uuid
    bruteforce.target_device = target_device
    bruteforce.started = int(time.time())
    bruteforce.progress = 0
    service.speed = speed
    service.running = True

    wrapper.session.commit()

    return success_scheme


@m.user_endpoint(path=["bruteforce", "status"], requires=standard_scheme)
@register_errors(service_exists("bruteforce"), device_online, device_accessible)
def status(data: dict, user: str, service: Service):
    if not service.running:
        return attack_not_running

    bruteforce: Bruteforce = wrapper.session.query(Bruteforce).get(service.uuid)
    bruteforce.update_progress(service.speed)

    return {**bruteforce.serialize}


@m.user_endpoint(path=["bruteforce", "stop"], requires=standard_scheme)
@register_errors(service_exists("bruteforce"), device_online, device_accessible)
def stop(data: dict, user: str, service: Service):
    if not service.running:
        return attack_not_running

    bruteforce: Bruteforce = wrapper.session.query(Bruteforce).get(service.uuid)

    target_device: str = bruteforce.target_device

    target_service: Service = wrapper.session.query(Service).filter_by(
        uuid=bruteforce.target_service, device=target_device
    ).first()

    bruteforce.update_progress(service.speed)

    progress: float = bruteforce.progress

    bruteforce.target_device = None
    bruteforce.target_service = None
    bruteforce.started = None
    bruteforce.progress = 0
    service.running = False
    wrapper.session.commit()

    stop_service(service.device, service.uuid, service.owner)

    access: bool = False
    if target_service is None:
        return service_not_found
    elif not target_service.running:
        return service_not_running
    elif random.random() + 0.1 < calculate_pos(progress):
        target_service.part_owner = user
        wrapper.session.commit()
        access: bool = True

    return {"ok": True, "access": access, "progress": progress, "target_device": target_device}
