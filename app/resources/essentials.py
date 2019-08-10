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


def change_miner_power(power: float, service_uuid: str, device_uuid: str) -> Tuple[float, float, float, float, float]:
    return game_content.dict2tuple(
        m.contact_microservice(
            "device",
            ["hardware", "scale"],
            {
                "service_uuid": service_uuid,
                "device_uuid": device_uuid,
                "cpu": config["services"]["miner"]["needs"]["cpu"] * power,
                "ram": config["services"]["miner"]["needs"]["ram"] * power,
                "gpu": config["services"]["miner"]["needs"]["gpu"] * power,
                "disk": config["services"]["miner"]["needs"]["disk"] * power,
                "network": config["services"]["miner"]["needs"]["network"] * power,
            },
        )
    )


def controls_device(device: str, user: str) -> bool:
    return m.contact_microservice("device", ["owner"], {"device_uuid": device})[
        "owner"
    ] == user or game_content.part_owner(device, user)


def exists_wallet(wallet: str) -> bool:
    return m.contact_microservice("currency", ["exists"], {"source_uuid": wallet})["exists"]


def is_miner(service_uuid: str) -> bool:
    return wrapper.session.query(Service).filter_by(uuid=service_uuid, name="miner").first() is not None


def calculate_mcs(power: int) -> float:
    return power * 2


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

    r_data: dict = {"device_uuid": data["device_uuid"], "service_uuid": uuid}

    given_per: Tuple[float, float, float, float, float] = game_content.dict2tuple(
        m.contact_microservice(
            "device", ["hardware", "register"], {**r_data, **config["services"][name]["needs"], "user": user}
        )
    )

    expected_per: Tuple[float, float, float, float, float] = game_content.dict2tuple(config["services"][name]["needs"])

    service: Service = Service.create(
        uuid, data["device_uuid"], user, name, config["services"][name]["speedm"](expected_per, given_per)
    )

    return service.serialize


def delete_one_service(service: Service):
    if service.name == "bruteforce":
        bruteforce: Bruteforce = wrapper.session.query(Bruteforce).get(service.uuid)
        wrapper.session.delete(bruteforce)
    elif service.name == "miner":
        miner: Miner = wrapper.session.query(Miner).get(service.uuid)
        update_miner(miner)
        wrapper.session.delete(miner)

    stop_service(service.device, service.uuid)
    wrapper.session.delete(service)
    wrapper.session.commit()


def stop_service(device_uuid: str, service_uuid: str) -> None:
    m.contact_microservice("device", ["hardware", "stop"], {"device_uuid": device_uuid, "service_uuid": service_uuid})


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
