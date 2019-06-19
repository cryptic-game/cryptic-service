from app import m, wrapper
from schemes import attack_scheme, invalid_request, success_scheme, standart_scheme, service_does_not_exists
from models.bruteforce import Bruteforce
from models.service import Service
import time
import random
from resources.game_content import calculate_pos


@m.user_endpoint(path=["bruteforce", "attack"], requires=attack_scheme)
def attack(user: str, data):
    target_device: str = data["target_device"]
    target_service_uuid: str = data["target_service"]

    service: Bruteforce = wrapper.session.query(Bruteforce).filter_by(uuid=data["service_uuid"]).first()
    target_service: Service = wrapper.session.query(Service).filter_by(uuid=target_service_uuid,
                                                                       device=target_device).first()

    service.use(target_service, target_device)

    return success_scheme


@m.user_endpoint(path=["bruteforce", "stop"], requires=standart_scheme)
def stop(user: str, data: dict):
    target_device: str = data["target_device"]
    target_service_uuid: str = data["target_service"]

    service: Bruteforce = wrapper.session.query(Bruteforce).filter_by(uuid=data["service_uuid"]).first()
    target_service: Service = wrapper.session.query(Service).filter_by(uuid=target_service_uuid,
                                                                       device=target_device).first()

    if service is None or target_service is None:
        return service_does_not_exists

    if isinstance(service.target_device, str) and isinstance(service.target_service, str) and len(
            service.target_device) > 1:
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

        return {"error": "you_first_have_to_start_an_attack"}
