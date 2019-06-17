from math import exp, sqrt

from app import m, wrapper
from models.service import Service
from resources import game_content


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
