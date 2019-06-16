from datetime import datetime
from typing import Union
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Float

from app import wrapper


class Miner(wrapper.Base):
    __tablename__: str = 'miner'

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    device: Union[Column, str] = Column(String(36))
    owner: Union[Column, str] = Column(String(36))
    wallet: Union[Column, str] = Column(String(36))
    running: Union[Column, bool] = Column(Boolean)
    power: Union[Column, int] = Column(Integer)
    started: Union[Column, datetime] = Column(DateTime)
    mined_coins: Union[Column, float] = Column(Float)

    @property
    def serialize(self):
        _: str = self.uuid
        d: dict = self.__dict__.copy()

        del d['_sa_instance_state']
        if d['started'] is not None:
            d['started'] = str(d['started'])

        return d

    @staticmethod
    def create(device: str, user: str, wallet: str) -> 'Miner':
        miner: Miner = Miner(
            uuid=str(uuid4()),
            device=device,
            owner=user,
            wallet=wallet,
            running=False,
            power=0,
            started=None,
            mined_coins=0
        )

        wrapper.session.add(miner)
        wrapper.session.commit()

        return miner
