from typing import Tuple
from uuid import uuid4

from app import m, wrapper
from models.bruteforce import Bruteforce
from models.miner import Miner
from models.service import Service
from resources import game_content
from schemes import invalid_request, wallet_not_found
from vars import config


def exists_device(device: str) -> bool:
    return m.contact_microservice("device", ["exist"], {"device_uuid": device})["exist"]


def change_miner_power(power: float, service_uuid: str, device_uuid: str, user: str) -> float:
    stop_service(device_uuid, service_uuid, user)

    microservice_response = m.contact_microservice(
        "device",
        ["hardware", "register"],
        {
            "user": user,
            "service_uuid": service_uuid,
            "device_uuid": device_uuid,
            "cpu": config["services"]["miner"]["needs"]["cpu"] * power,
            "ram": config["services"]["miner"]["needs"]["ram"] * power,
            "gpu": config["services"]["miner"]["needs"]["gpu"] * power,
            "disk": config["services"]["miner"]["needs"]["disk"] * power,
            "network": config["services"]["miner"]["needs"]["network"] * power,
        },
    )
    if "error" in microservice_response:
        return -1

    given_per: Tuple[float, float, float, float, float] = game_content.dict2tuple(microservice_response)

    expected_per: Tuple[float, float, float, float, float] = game_content.dict2tuple(
        config["services"]["miner"]["needs"]
    )

    return config["services"]["miner"]["speedm"](expected_per, given_per)


def controls_device(device: str, user: str) -> bool:
    return get_device_owner(device) == user or game_content.part_owner(device, user)


def check_device_online(device: str) -> bool:
    return m.contact_microservice("device", ["ping"], {"device_uuid": device}).get("online", False)


def get_device_owner(device: str) -> str:
    return m.contact_microservice("device", ["owner"], {"device_uuid": device}).get("owner")


def exists_wallet(wallet: str) -> bool:
    return m.contact_microservice("currency", ["exists"], {"source_uuid": wallet})["exists"]


def update_miner(miner: Miner):
    mined_coins: int = miner.update_miner()
    if mined_coins > 0:
        m.contact_microservice(
            "currency", ["put"], {"destination_uuid": miner.wallet, "amount": mined_coins, "create_transaction": False}
        )


def create_service(name: str, data: dict, user: str):
    uuid: str = str(uuid4())

    if name == "bruteforce":
        Bruteforce.create(uuid)
    elif name == "miner":
        # First check for name then validate for special information
        if "wallet_uuid" not in data:
            return invalid_request
        wallet_uuid: str = data["wallet_uuid"]
        if not isinstance(wallet_uuid, str):
            return invalid_request
        if not exists_wallet(wallet_uuid):
            return wallet_not_found
        Miner.create(uuid, data["wallet_uuid"])

    speed: float = 0
    running: bool = False
    if config["services"][name]["auto_start"]:
        speed: float = register_service(data["device_uuid"], uuid, name, user)
        if speed == -1:
            speed: float = 0
        else:
            running: bool = True

    service: Service = Service.create(uuid, data["device_uuid"], user, name, speed, running)

    return service.serialize


def delete_one_service(service: Service):
    if service.name == "bruteforce":
        bruteforce: Bruteforce = wrapper.session.query(Bruteforce).get(service.uuid)
        wrapper.session.delete(bruteforce)
    elif service.name == "miner":
        miner: Miner = wrapper.session.query(Miner).get(service.uuid)
        update_miner(miner)
        wrapper.session.delete(miner)

    stop_service(service.device, service.uuid, service.owner)
    wrapper.session.delete(service)
    wrapper.session.commit()


def register_service(device_uuid: str, service_uuid: str, name: str, user: str) -> float:
    r_data: dict = {"device_uuid": device_uuid, "service_uuid": service_uuid}

    microservice_response: dict = m.contact_microservice(
        "device", ["hardware", "register"], {**r_data, **config["services"][name]["needs"], "user": user}
    )

    if "error" in microservice_response:
        return -1

    given_per: Tuple[float, float, float, float, float] = game_content.dict2tuple(microservice_response)

    expected_per: Tuple[float, float, float, float, float] = game_content.dict2tuple(config["services"][name]["needs"])

    return config["services"][name]["speedm"](expected_per, given_per)


def stop_service(device_uuid: str, service_uuid: str, user: str):
    m.contact_microservice(
        "device", ["hardware", "stop"], {"device_uuid": device_uuid, "service_uuid": service_uuid, "user": user}
    )


def stop_services(device_uuid: str):
    for service in wrapper.session.query(Service).filter_by(device=device_uuid):
        if service.name == "bruteforce":
            bruteforce: Bruteforce = wrapper.session.query(Bruteforce).get(service.uuid)
            bruteforce.target_device = None
            bruteforce.target_service = None
            bruteforce.started = None
        elif service.name == "miner":
            miner: Miner = wrapper.session.query(Miner).get(service.uuid)
            update_miner(miner)
            miner.started = None
        service.running = False

    wrapper.session.commit()


def delete_services(device_uuid: str):
    for service in wrapper.session.query(Service).filter_by(device=device_uuid):
        delete_one_service(service)
