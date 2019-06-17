from typing import Union
from uuid import uuid4

from sqlalchemy import Column, Integer, String, Boolean

from app import wrapper
from models.bruteforce import Bruteforce
from models.miner import Miner
from vars import config


class Service(wrapper.Base):
    __tablename__: str = "service"

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    device: Union[Column, str] = Column(String(36))
    owner: Union[Column, str] = Column(String(36), nullable=False)
    name: Union[Column, str] = Column(String(32))
    running: Union[Column, bool] = Column(Boolean)
    running_port: Union[Column, int] = Column(Integer)
    consumption: Union[Column, int] = Column(Integer)
    part_owner: Union[Column, str] = Column(String(36))

    @property
    def serialize(self):
        _: str = self.uuid
        d: dict = self.__dict__.copy()

        del d['_sa_instance_state']

        return d

    @staticmethod
    def create(device: str, owner: str, name: str) -> 'Service':
        """
        Creates a new service.

        :param device: uuid of the associated device
        :param owner: uuid of the owner
        :param name: name of the service
        :return: New DeviceModel
        """

        uuid: str = str(uuid4())

        service = Service(
            uuid=uuid,
            owner=owner,
            device=device,
            running=config["services"][name]["default_port"] is not None,
            name=name,
            running_port=config["services"][name]["default_port"],
            consumption=config["services"][name]["consumption"]
        )

        wrapper.session.add(service)
        wrapper.session.commit()

        return service

    def check_access(self, user: str) -> bool:
        return user in (self.owner, self.part_owner)

    def public_data(self):
        return {"uuid": self.uuid, "name": self.name, "running_port": self.running_port, "device": self.device}

    def delete(self):
        if self.name == "bruteforce":
            bruteforce: Bruteforce = wrapper.session.query(Bruteforce).filter_by(uuid=self.uuid).first()
            wrapper.session.delete(bruteforce)
        elif self.name == "miner":
            miner: Miner = wrapper.session.query(Miner).filter_by(uuid=self.uuid).first()
            wrapper.session.delete(miner)

        wrapper.session.delete(self)
        wrapper.session.commit()
