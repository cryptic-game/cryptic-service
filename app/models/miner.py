import time
from typing import Union

from sqlalchemy import Column, String, BigInteger, Float

from app import wrapper


class Miner(wrapper.Base):
    __tablename__: str = "service_miner"

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    wallet: Union[Column, str] = Column(String(36))
    started: Union[Column, int] = Column(BigInteger)
    power: Union[Column, int] = Column(Float)

    @property
    def serialize(self) -> dict:
        _: str = self.uuid
        d: dict = self.__dict__.copy()

        del d["_sa_instance_state"]

        return d

    @staticmethod
    def create(uuid: str, wallet: str) -> "Miner":
        miner: Miner = Miner(uuid=uuid, wallet=wallet, started=None, power=0)

        wrapper.session.add(miner)
        wrapper.session.commit()

        return miner

    def update_miner(self) -> int:
        from resources.service import Service

        service: Service = wrapper.session.query(Service).get(self.uuid)
        if not service.running:
            return 0

        now: int = int(time.time())
        mined_coins: int = int((now - self.started) * service.speed)
        if mined_coins > 0:
            self.started: int = now
            wrapper.session.commit()

        return mined_coins
