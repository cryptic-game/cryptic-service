import time
from typing import Union

from sqlalchemy import Column, BigInteger, String, Float

from app import wrapper


class Bruteforce(wrapper.Base):
    __tablename__: str = "service_bruteforce"

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    started: Union[Column, int] = Column(BigInteger)
    target_service: Union[Column, str] = Column(String(36))
    target_device: Union[Column, str] = Column(String(36))
    progress: Union[Column, float] = Column(Float)

    @property
    def serialize(self):
        _: str = self.uuid
        d: dict = self.__dict__.copy()

        del d["_sa_instance_state"]

        return d

    @staticmethod
    def create(uuid: str) -> "Bruteforce":
        """
        Creates a new service.
        :param uuid: uuid of the service
        :return: New DeviceModel
        """

        service = Bruteforce(uuid=uuid, started=None, target_service=None, target_device=None, progress=0)

        wrapper.session.add(service)
        wrapper.session.commit()

        return service

    def update_progress(self, speed: float):
        if self.started is not None:
            now: int = int(time.time())
            self.progress += (now - self.started) * speed
            self.started = now
            wrapper.session.commit()
