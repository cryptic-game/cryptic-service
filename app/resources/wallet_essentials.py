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


def isminer(service_uuid: str) -> bool:
    return wrapper.session.query(Service).filter_by(uuid=service_uuid, name="miner").first() is not None


def checkrunning(service_uuid: str):
    return wrapper.session.query(Service).filter_by(uuid=service_uuid).first().running
