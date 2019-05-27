import time
from typing import NoReturn
from typing import Union
from uuid import uuid4

from sqlalchemy import Column, Integer, String, Boolean

from app import wrapper
from vars import config


class Service(wrapper.Base):
    __tablename__: str = "service"

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    device: Union[Column, str] = Column(String(36))
    owner: Union[Column, str] = Column(String(36), nullable=False)
    name: Union[Column, str] = Column(String(32))
    running: Union[Column, bool] = Column(Boolean)
    action: Union[Column, int] = Column(Integer)
    target_service: Union[Column, str] = Column(String(36))
    target_device: Union[Column, str] = Column(String(36))
    part_owner: Union[Column, str] = Column(String(36))
    running_port: Union[Column, int] = Column(Integer)

    @property
    def serialize(self):
        _: str = self.uuid
        d: dict = self.__dict__.copy()

        del d['_sa_instance_state']

        return d

    @staticmethod
    def create(user: str, device: str, name: str) -> 'Service':
        """
        Creates a new service.
        :param name:
        :param user: The owner's uuid
        :param device: devices uuid
        :return: New DeviceModel
        """

        uuid: str = str(uuid4())

        default_port: int = config["services"][name]["default_port"]

        service = Service(uuid=uuid, owner=user, device=device, running=True, name=name, running_port=default_port)

        wrapper.session.add(service)
        wrapper.session.commit()

        return service

    def use(self, data: dict) -> NoReturn:
        if self.name == "bruteforce":
            self.target_service: str = data["target_service"]
            self.target_device: str = data["target_device"]
            self.action: int = int(time.time())

    def public_data(self):
        return {"uuid": self.uuid, "name": self.name, "running_port": self.running_port, "device": self.device}


wrapper.Base.metadata.create_all(wrapper.engine)
