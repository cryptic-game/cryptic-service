import time
from typing import Union
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Float
from vars import config
from app import wrapper
from math import sqrt, exp


class Miner(wrapper.Base):
    __tablename__: str = 'miner'

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    wallet: Union[Column, str] = Column(String(36))
    started: Union[Column, int] = Column(Integer)

    @property
    def serialize(self):
        _: str = self.uuid
        d: dict = self.__dict__.copy()

        del d['_sa_instance_state']
        if d['started'] is not None:
            d['started'] = str(d['started'])

        return d

    @staticmethod
    def create(user: str, wallet: str) -> 'Miner':
        miner: Miner = Miner(
            uuid=str(uuid4()),
            wallet=wallet,
            started=None,
        )

        wrapper.session.add(miner)
        wrapper.session.commit()

        return miner

    def calculate_mcs(self) -> float:
        a: int = config["services"]["miner"]["a"]
        b: int = config["services"]["miner"]["b"]
        c: int = config["services"]["miner"]["c"]
        x: int = 80  # const because should be definded by the strength of the device

        return (b * (3 + a) / 10500 + sqrt(a * b * c) / 30000) * (1 - exp(-0.0231 * x))

    def update_miner(self):
        from resources.wallet_essentials import checkrunning
        if not checkrunning(self.uuid):
            return False

        mined_coins: int = self.calculate_mcs() * (int(time.time()) - self.started)
        self.started = int(time.time())
        wrapper.session.commit()

        return mined_coins

    def show_miner(self):
        from resources.wallet_essentials import checkrunning
        if not checkrunning(self.uuid):
            return False

        mined_coins: int = self.calculate_mcs() * (int(time.time()) - self.started)

        return mined_coins


wrapper.Base.metadata.create_all(wrapper.engine)
