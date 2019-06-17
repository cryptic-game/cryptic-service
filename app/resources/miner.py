from scheme import UUID, Integer
from app import m
from schemes import *
from resources.wallet_essentials import *
from models.miner import Miner


@m.user_endpoint(path=["miner", "get"], requires={"device_uuid": UUID()})
def get(data: dict, user: str) -> dict:
    miner: Miner = wrapper.session.query(Miner).filter_by(device=data["device_uuid"]).first()
    if miner is None:
        return miner_does_not_exist
    mined_coins: int = miner.show_miner()
    if mined_coins is False:
        return {"error": "miner is not running"}
    return {"coins": mined_coins}


@m.user_endpoint(path=["miner", "list"], requires={"wallet_uuid": UUID()})
def list_miners(data: dict, user: str) -> dict:
    return {"miners": [
        miner.serialize for miner in
        wrapper.session.query(Miner).filter_by(wallet=data["wallet_uuid"])
    ]}


@m.microservice_endpoint(path=["miner", "collect"])
def collect(data: dict, microservice: str) -> dict:
    wallet: str = data["wallet_uuid"]

    coins: dict = {}
    for miner in wrapper.session.query(Miner).filter_by(wallet=wallet).all():
        mined_coins: int = miner.update_miner()
        wrapper.session.commit()

        coins.update({str(miner.uuid): mined_coins})
    return coins
