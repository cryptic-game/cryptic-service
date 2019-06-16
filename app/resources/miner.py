from datetime import datetime
from math import sqrt, exp
from typing import List

from scheme import UUID, Integer

from app import m, wrapper
from models.miner import Miner
from resources import game_content
from schemes import *


def exists_device(device: str) -> bool:
    return m.contact_microservice("device", ["exist"], {"device_uuid": device})["exist"]


def controls_device(device: str, user: str) -> bool:
    return m.contact_microservice("device", ["owner"], {"device_uuid": device})["owner"] == user or \
           game_content.part_owner(device, user)


def exists_wallet(wallet: str) -> bool:
    return m.contact_microservice("currency", ["exists"], {"source_uuid": wallet})["exists"]


def calculate_mcs(miner: Miner) -> float:
    a: int = 1
    b: int = 800
    c: int = 512
    x: int = miner.power

    return (b * (3 + a) / 10500 + sqrt(a * b * c) / 30000) * (1 - exp(-0.0231 * x))


def update_miner(miner: Miner):
    if not miner.running:
        return
    mcs: float = calculate_mcs(miner)
    now: datetime = datetime.now()
    miner.mined_coins += mcs * (now - miner.started).total_seconds()
    miner.started = now
    wrapper.session.commit()


@m.user_endpoint(path=["miner", "create"], requires={
    "device_uuid": UUID(),
    "wallet_uuid": UUID()
})
def create(data: dict, user: str) -> dict:
    device: str = data["device_uuid"]
    wallet: str = data["wallet_uuid"]

    if not exists_device(device):
        return device_does_not_exist

    if not controls_device(device, user):
        return permission_denied

    if not exists_wallet(wallet):
        return wallet_does_not_exist

    if wrapper.session.query(Miner).filter_by(device=device).first() is not None:
        return multiple_miners

    return Miner.create(device, user, wallet).serialize


@m.user_endpoint(path=["miner", "get"], requires={
    "device_uuid": UUID()
})
def get(data: dict, user: str) -> dict:
    miner: Miner = wrapper.session.query(Miner).filter_by(device=data["device_uuid"]).first()
    if miner is None:
        return miner_does_not_exist
    update_miner(miner)
    return miner.serialize


@m.user_endpoint(path=["miner", "list"], requires={
    "wallet_uuid": UUID()
})
def list_miners(data: dict, user: str) -> dict:
    return {"miners": [
        miner.serialize for miner in
        wrapper.session.query(Miner).filter_by(wallet=data["wallet_uuid"])
    ]}


@m.user_endpoint(path=["miner", "power"], requires={
    "device_uuid": UUID(),
    "miner_uuid": UUID(),
    "power": Integer(minimum=0, maximum=100)
})
def set_power(data: dict, user: str) -> dict:
    device: str = data["device_uuid"]
    power: int = data["power"]

    if not exists_device(device):
        return device_does_not_exist
    if not controls_device(device, user):
        return permission_denied

    miner: Miner = wrapper.session.query(Miner).filter_by(device=device, uuid=(data["miner_uuid"])).first()
    if miner is None:
        return miner_does_not_exist

    update_miner(miner)

    miner.power: int = power
    if power >= 10:
        miner.running: bool = True
        miner.started: datetime = datetime.now()
    else:
        miner.running: bool = False
        miner.started: datetime = None
    wrapper.session.commit()

    return miner.serialize


@m.user_endpoint(path=["miner", "delete"], requires={
    "device_uuid": UUID(),
    "miner_uuid": UUID()
})
def delete(data: dict, user: str) -> dict:
    miner: Miner = wrapper.session.query(Miner).filter_by(device=data["device_uuid"], uuid=data["miner_uuid"]).first()
    if miner is None:
        return miner_does_not_exist

    wrapper.session.delete(miner)
    wrapper.session.commit()

    return success_scheme


@m.microservice_endpoint(path=["miner", "collect"])
def collect(data: dict, microservice: str) -> dict:
    wallet: str = data["wallet_uuid"]

    coins: List[dict] = []
    for miner in wrapper.session.query(Miner).filter_by(wallet=wallet):
        update_miner(miner)
        mined_coins: int = int(miner.mined_coins)
        miner.mined_coins -= mined_coins
        wrapper.session.commit()

        coins.append({
            "miner_uuid": miner.uuid,
            "amount": mined_coins
        })
    return {"coins": coins}
