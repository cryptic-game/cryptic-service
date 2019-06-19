from math import exp, sqrt

from app import m, wrapper
from models.service import Service
from resources import game_content
from models.miner import Miner
from models.bruteforce import Bruteforce
from schemes import invalid_request, wallet_does_not_exist


def exists_device(device: str) -> bool:
    return m.contact_microservice("device", ["exist"], {"device_uuid": device})["exist"]


def controls_device(device: str, user: str) -> bool:
    return m.contact_microservice("device", ["owner"], {"device_uuid": device})["owner"] == user or \
           game_content.part_owner(device, user)


def exists_wallet(wallet: str) -> bool:
    return m.contact_microservice("currency", ["exists"], {"source_uuid": wallet})["exists"]


def is_miner(service_uuid: str) -> bool:
    return wrapper.session.query(Service).filter_by(uuid=service_uuid, name="miner").first() is not None


def calculate_mcs(device: str, power: int) -> float:
    cores: int = 1
    clock_rate: int = 800
    ram: int = 512
    return (clock_rate * (3 + cores) / 10500 + sqrt(cores * clock_rate * ram) / 30000) * (1 - exp(-0.0231 * power))


def create(name: str, data: dict):
    service: Service = Service.create(data["device_uuid"], data["user"], name)

    if name == "bruteforce":
        Bruteforce.create(data["user"], service.uuid)
    elif name == "miner":

        # First check for name than validate for special information

        if "wallet_uuid" not in data:
            return invalid_request
        wallet_uuid: str = data["wallet_uuid"]
        if not isinstance(wallet_uuid, str):
            return invalid_request
        if not exists_wallet(wallet_uuid):
            return wallet_does_not_exist
        Miner.create(service.uuid, data["wallet_uuid"])

    return service.serialize
