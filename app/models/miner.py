import time
from typing import Union

from sqlalchemy import Column, String, Integer, Float

from app import wrapper


class Miner(wrapper.Base):
    __tablename__: str = 'miner'

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    wallet: Union[Column, str] = Column(String(36))
    started: Union[Column, int] = Column(Integer)  # This Fuck is UNIX Time and we realy dont care about ms.
    power: Union[Column, int] = Column(Integer)

    @property
    def serialize(self) -> dict:
        _: str = self.uuid
        d: dict = self.__dict__.copy()

        del d['_sa_instance_state']
        if d['started'] is not None:
            d['started'] = str(d['started'])

        return d

    @staticmethod
    def create(uuid: str, wallet: str) -> 'Miner':
        miner: Miner = Miner(
            uuid=uuid,
            wallet=wallet,
            started=None,
            power=0
        )

        wrapper.session.add(miner)
        wrapper.session.commit()

        return miner

    def update_miner(self) -> int:
        from resources.essentials import calculate_mcs
        from resources.service import Service

        service: Service = wrapper.session.query(Service).get(self.uuid)
        if not service.running:
            return 0

        now: float = time.time()
        mined_coins: int = int(calculate_mcs(service.device, self.power) * (now - self.started))
        if mined_coins > 0:
            self.started = now
            wrapper.session.commit()

        return mined_coins
