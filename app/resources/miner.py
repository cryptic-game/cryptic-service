import time
from typing import Dict

from scheme import UUID, Integer

from app import m, wrapper
from models.miner import Miner
from models.service import Service
from resources.essentials import exists_device, controls_device
from schemes import *


@m.user_endpoint(path=["miner", "get"], requires={
    "service_uuid": UUID()
})
def get(data: dict, user: str) -> dict:
    miner: Miner = wrapper.session.query(Miner).filter_by(uuid=data["service_uuid"]).first()
    if miner is None:
        return miner_does_not_exist
    miner.update_miner()
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
    "service_uuid": UUID(),
    "power": Integer(minimum=0, maximum=100)
})
def set_power(data: dict, user: str) -> dict:
    service_uuid: str = data["service_uuid"]
    power: int = data["power"]

    miner: Miner = wrapper.session.query(Miner).filter_by(uuid=service_uuid).first()
    if miner is None:
        return miner_does_not_exist

    service: Service = wrapper.session.query(Service).filter_by(uuid=service_uuid).first()
    if not exists_device(service.device):
        return device_does_not_exist
    if not controls_device(service.device, user):
        return permission_denied

    miner.update_miner()

    miner.power: int = power
    if power >= 10:
        service.running: bool = True
        miner.started: float = time.time()
    else:
        service.running: bool = False
        miner.started: float = None
    wrapper.session.commit()

    return miner.serialize


@m.microservice_endpoint(path=["miner", "collect"])
def collect(data: dict, microservice: str) -> dict:
    wallet: str = data["wallet_uuid"]

    coins: Dict[str, int] = {}
    for miner in wrapper.session.query(Miner).filter_by(wallet=wallet).all():
        miner.update_miner()

        mined_coins: int = int(miner.mined_coins)
        if mined_coins == 0:
            continue
        miner.mined_coins -= mined_coins
        wrapper.session.commit()

        coins[miner.uuid] = mined_coins
    return coins
