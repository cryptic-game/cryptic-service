from typing import Optional

from scheme import UUID
from sqlalchemy import func

import resources.game_content as game_content
from app import m, wrapper
from models.bruteforce import Bruteforce
from models.miner import Miner
from models.service import Service
from resources.essentials import exists_device, controls_device, exists_wallet
from schemes import *
from vars import config

switch: dict = {  # this is just for tools, its a more smooth way of a "switch" statement
    "bruteforce": game_content.bruteforce,
    "portscan": game_content.portscan
}


@m.user_endpoint(path=["public_info"], requires={
    "device_uuid": UUID(),
    "service_uuid": UUID()
})
def public_info(data: dict, user: str) -> dict:
    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                          device=data["device_uuid"]).first()
    if service is None or service.running_port is None or not service.running:
        return unknown_service
    return service.public_data()


@m.user_endpoint(path=["use"], requires=None)
def use(data: dict, user: str) -> dict:
    if "device_uuid" not in data or "service_uuid" not in data:
        return invalid_request

    device_uuid: str = data["device_uuid"]
    service_uuid: str = data["service_uuid"]
    if not isinstance(device_uuid, str) or not isinstance(service_uuid, str):
        return invalid_request

    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=service_uuid,
                                                                          device=device_uuid).first()

    if service is None or (service.owner != user
                           and not game_content.part_owner(device_uuid, user)):
        return unknown_service

    if service.name not in switch:
        return service_cannot_be_used

    return switch[service.name](data, user)


@m.user_endpoint(path=["private_info"], requires={
    "device_uuid": UUID(),
    "service_uuid": UUID()
})
def private_info(data: dict, user: str) -> dict:
    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                          device=data["device_uuid"]).first()

    if service is None:
        return unknown_service

    if not service.check_access(user):
        return permission_denied

    return service.serialize


@m.user_endpoint(path=["turn_off_on"], requires={
    "device_uuid": UUID(),
    "service_uuid": UUID()
})
def turnoff_on(data: dict, user: str) -> dict:
    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=data["service_uuid"],
                                                                          device=data["device_uuid"]).first()

    if service is None:
        return service_does_not_exists

    if user != service.owner:
        return permission_denied

    service.running: bool = not service.running

    wrapper.session.commit()

    return service.serialize


@m.user_endpoint(path=["delete"], requires={
    "device_uuid": UUID(),
    "service_uuid": UUID()
})
def delete_service(data: dict, user: str) -> dict:
    device_uuid: str = data["device_uuid"]
    service_uuid: str = data["service_uuid"]
    service: Optional[Service] = wrapper.session.query(Service).filter_by(uuid=service_uuid,
                                                                          device=device_uuid).first()

    if service is None:
        return service_does_not_exists

    if user != m.contact_microservice("device", ["owner"], {"device_uuid": device_uuid})["owner"]:
        return permission_denied

    if service.name == "bruteforce":
        bruteforce: Bruteforce = wrapper.session.query(Bruteforce).filter_by(uuid=service.uuid).first()
        wrapper.session.delete(bruteforce)
    elif service.name == "miner":
        miner: Miner = wrapper.session.query(Miner).filter_by(uuid=service.uuid).first()
        mined_coins: int = miner.update_miner()
        if mined_coins > 0:
            m.contact_microservice("currency", ["put"], {
                "destination_uuid": miner.wallet,
                "amount": mined_coins,
                "create_transaction": False
            })
        wrapper.session.delete(miner)

    wrapper.session.delete(service)
    wrapper.session.commit()

    return {"ok": True}


@m.user_endpoint(path=["list"], requires={
    "device_uuid": UUID()
})
def list_services(data: dict, user: str) -> dict:
    if not controls_device(data["device_uuid"], user):
        return permission_denied

    return {
        "services": [
            service.serialize for service in
            wrapper.session.query(Service).filter_by(device=data["device_uuid"]).all()
        ]
    }


@m.user_endpoint(path=["create"], requires=None)
def create(data: dict, user: str) -> dict:
    if "device_uuid" not in data or "name" not in data:
        return invalid_request

    device_uuid: str = data["device_uuid"]
    name: str = data["name"]

    wallet_uuid: str = None
    if name == "miner":
        if "wallet_uuid" not in data:
            return invalid_request
        wallet_uuid: str = data["wallet_uuid"]
        if not isinstance(wallet_uuid, str):
            return invalid_request
        if not exists_wallet(wallet_uuid):
            return wallet_does_not_exist

    if not isinstance(device_uuid, str) or not isinstance(name, str):
        return invalid_request

    if name not in config["services"].keys():
        return service_is_not_supported

    if not exists_device(device_uuid):
        return device_does_not_exist

    if not controls_device(device_uuid, user):
        return permission_denied

    service_count: int = wrapper.session.query(func.count(Service.name)).filter(
        Service.owner == user,
        Service.device == device_uuid,
        Service.name == name
    ).first()[0]
    if service_count != 0:
        return multiple_services

    service: Service = Service.create(device_uuid, user, name)

    if name == "bruteforce":
        Bruteforce.create(user, service.uuid)
    elif name == "miner":
        Miner.create(service.uuid, wallet_uuid)

    return service.serialize


@m.user_endpoint(path=["part_owner"], requires={
    "device_uuid": UUID()
})
def part_owner(data: dict, user: str) -> dict:
    return {"ok": game_content.part_owner(data["device_uuid"], user)}


@m.microservice_endpoint(path=["check_part_owner"])
def check_part_owner(data: dict, microservice: str) -> dict:
    # all these requests are trusted
    return {"ok": game_content.part_owner(data["device_uuid"], data["user_uuid"])}
