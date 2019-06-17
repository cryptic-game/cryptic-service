import time
from typing import NoReturn
from typing import Union, Dict
from uuid import uuid4

from sqlalchemy import Column, Integer, String, Boolean

from app import wrapper
from vars import config

from models.miner import Miner
from models.bruteforce import Bruteforce


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
    def create(data: dict) -> 'Service':
        """
        Creates a new service.
        :param data:
        :return: New DeviceModel
        """

        uuid: str = str(uuid4())

        default_port: int = config["services"][data["name"]]["default_port"]

        service = Service(uuid=uuid, owner=data["user"], device=data["device_uuid"], running=True, name=data["name"],
                          running_port=default_port, consumption=config["services"][data["name"]]["consumption"])

        wrapper.session.add(service)

        if data["name"] == "bruteforce":
            Bruteforce.create(data["user"], uuid)
        elif data["name"] == "miner":
            if "wallet_uuid" not in data:
                return {"error": "wallet_uuid_is_missing"}
            Miner.create(data["user"], data["wallet_uuid"])

        # Tools that dont have to save special information and only the existens is important dont need an extra Class.

        wrapper.session.commit()

        return Union[Service, Dict[str, str]]

    def use(self, data: dict) -> NoReturn:
        if self.name == "bruteforce":
            self.target_service: str = data["target_service"]
            self.target_device: str = data["target_device"]
            self.action: int = int(time.time())

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


wrapper.Base.metadata.create_all(wrapper.engine)
