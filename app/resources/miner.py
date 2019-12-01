import time
from typing import List

from cryptic import register_errors

from app import m, wrapper
from models.miner import Miner
from models.service import Service
from resources.errors import service_exists, device_online, device_accessible
from resources.essentials import exists_wallet, update_miner, change_miner_power, stop_service, check_device_online
from schemes import (
    wallet_not_found,
    service_scheme,
    wallet_scheme,
    miner_set_wallet_scheme,
    miner_set_power_scheme,
    could_not_start_service,
    success_scheme,
)


@m.user_endpoint(path=["miner", "get"], requires=service_scheme)
@register_errors(service_exists("miner", device_required=False), device_online, device_accessible)
def get(data: dict, user: str, service: Service) -> dict:
    return wrapper.session.query(Miner).get(service.uuid).serialize


@m.user_endpoint(path=["miner", "list"], requires=wallet_scheme)
def list_miners(data: dict, user: str) -> dict:
    miners: List[dict] = []
    for miner in wrapper.session.query(Miner).filter_by(wallet=data["wallet_uuid"]):
        service: Service = wrapper.session.query(Service).get(miner.uuid)
        if not check_device_online(service.device):
            continue
        miners.append({"miner": miner.serialize, "service": service.serialize})
    return {"miners": miners}


@m.user_endpoint(path=["miner", "wallet"], requires=miner_set_wallet_scheme)
@register_errors(service_exists("miner", device_required=False), device_online, device_accessible)
def set_wallet(data: dict, user: str, service: Service) -> dict:
    wallet_uuid: str = data["wallet_uuid"]

    if not exists_wallet(wallet_uuid):
        return wallet_not_found

    miner: Miner = wrapper.session.query(Miner).get(service.uuid)

    update_miner(miner)

    miner.wallet = wallet_uuid
    wrapper.session.commit()

    return miner.serialize


@m.user_endpoint(path=["miner", "power"], requires=miner_set_power_scheme)
@register_errors(service_exists("miner", device_required=False), device_online, device_accessible)
def set_power(data: dict, user: str, service: Service) -> dict:
    miner: Miner = wrapper.session.query(Miner).get(service.uuid)

    if not exists_wallet(miner.wallet):
        return wallet_not_found

    power: int = data["power"]

    update_miner(miner)

    speed: float = change_miner_power(power, service.uuid, service.device, service.owner)
    if speed == -1:
        return could_not_start_service

    service.speed = speed
    service.running = power > 0
    miner.power = power
    if service.running:
        miner.started = int(time.time() * 1000)
    else:
        miner.started = None

    wrapper.session.commit()

    return miner.serialize


@m.microservice_endpoint(path=["miner", "stop"])
def miner_stop(data: dict, microservice: str) -> dict:
    for miner in wrapper.session.query(Miner).filter_by(wallet=data["wallet_uuid"]):
        service: Service = wrapper.session.query(Service).filter_by(uuid=miner.uuid).first()

        if service.running:
            stop_service(service.device, service.uuid, service.owner)

        service.running = False
        miner.started = None

    wrapper.session.commit()

    return success_scheme


@m.microservice_endpoint(path=["miner", "collect"])
def collect(data: dict, microservice: str) -> dict:
    return {
        "coins": sum(
            miner.update_miner() for miner in wrapper.session.query(Miner).filter_by(wallet=data["wallet_uuid"])
        )
    }
