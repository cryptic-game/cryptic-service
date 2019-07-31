from math import exp, sqrt
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


def controls_device(device: str, user: str) -> bool:
    return m.contact_microservice("device", ["owner"], {"device_uuid": device})[
        "owner"
    ] == user or game_content.part_owner(device, user)


def exists_wallet(wallet: str) -> bool:
    return m.contact_microservice("currency", ["exists"], {"source_uuid": wallet})["exists"]


def is_miner(service_uuid: str) -> bool:
    return wrapper.session.query(Service).filter_by(uuid=service_uuid, name="miner").first() is not None


def calculate_mcs(device: str, power: int) -> float:
    cores: int = 1
    clock_rate: int = 800
    ram: int = 512
    return (clock_rate * (3 + cores) / 10500 + sqrt(cores * clock_rate * ram) / 30000) * (1 - exp(-0.0231 * power))


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

    service: Service = Service.create(uuid, data["device_uuid"], user, name)

    r_data: dict = {"device_uuid": service.device, "service_uuid": service.uuid}

    given_per: Tuple[float, float, float, float, float] = game_content.dict2tuple(
        m.contact_microservice("device", ["hardware", "register"], {**r_data, **config["services"][name]["needs"]})
    )

    expected_per: Tuple[float, float, float, float, float] = game_content.dict2tuple(config["services"][name]["needs"])

    speed: float = game_content.calculate_speed(expected_per, given_per)

    wrapper.session.commit()

    service.speed = speed
    wrapper.session.commit()
    return service.serialize
