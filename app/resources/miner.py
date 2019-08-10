from typing import Tuple

from scheme import Float, UUID

from app import m, wrapper
from models.miner import Miner
from models.service import Service
from resources.essentials import (
    exists_device,
    controls_device,
    exists_wallet,
    update_miner,
    change_miner_power,
    calculate_mcs,
)
from resources.game_content import calculate_speed, dict2tuple
from vars import config
from schemes import miner_not_found, device_not_found, wallet_not_found, permission_denied


@m.user_endpoint(path=["miner", "get"], requires={"service_uuid": UUID()})
def get(data: dict, user: str) -> dict:
    miner: Miner = wrapper.session.query(Miner).filter_by(uuid=data["service_uuid"]).first()
    if miner is None:
        return miner_not_found
    return miner.serialize


@m.user_endpoint(path=["miner", "list"], requires={"wallet_uuid": UUID()})
def list_miners(data: dict, user: str) -> dict:
    return {"miners": [miner.serialize for miner in wrapper.session.query(Miner).filter_by(wallet=data["wallet_uuid"])]}


@m.user_endpoint(path=["miner", "wallet"], requires={"service_uuid": UUID(), "wallet_uuid": UUID()})
def set_wallet(data: dict, user: str) -> dict:
    service_uuid: str = data["service_uuid"]
    wallet_uuid: str = data["wallet_uuid"]

    miner: Miner = wrapper.session.query(Miner).filter_by(uuid=service_uuid).first()
    if miner is None:
        return miner_not_found

    service: Service = wrapper.session.query(Service).filter_by(uuid=service_uuid).first()
    if not exists_device(service.device):
        return device_not_found
    if not controls_device(service.device, user):
        return permission_denied

    if not exists_wallet(wallet_uuid):
        return wallet_not_found

    update_miner(miner)

    miner.wallet = wallet_uuid
    wrapper.session.commit()

    return miner.serialize


@m.user_endpoint(path=["miner", "power"], requires={"service_uuid": UUID(), "power": Float(minimum=0.0, maximum=1.0)})
def set_power(data: dict, user: str) -> dict:
    service_uuid: str = data["service_uuid"]
    power: int = data["power"]

    miner: Miner = wrapper.session.query(Miner).filter_by(uuid=service_uuid).first()
    if miner is None:
        return miner_not_found

    service: Service = wrapper.session.query(Service).filter_by(uuid=service_uuid).first()
    if not exists_device(service.device):
        return device_not_found
    if not controls_device(service.device, user):
        return permission_denied

    update_miner(miner)

    new: Tuple[float, float, float, float, float] = change_miner_power(power, service.uuid, service.device)

    service.speed = config["services"][service.name]["speedm"](dict2tuple(config["services"]["miner"]["needs"]), new)
    miner.mcs = calculate_mcs(power)
    miner.power = power

    wrapper.session.commit()

    return miner.serialize


@m.microservice_endpoint(path=["miner", "collect"])
def collect(data: dict, microservice: str) -> dict:
    return {
        "coins": sum(
            miner.update_miner() for miner in wrapper.session.query(Miner).filter_by(wallet=data["wallet_uuid"])
        )
    }
