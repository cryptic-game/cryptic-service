from objects import session, Base, engine
from uuid import uuid4
import random
import time
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import MetaData
from vars import config
from typing import Optional, List

class Service(Base):
    __tablename__: str = "service"

    uuid: Column = Column(String(36), primary_key=True, unique=True)
    device: Column = Column(String(36), primary_key=True, unique=True)
    owner: Column = Column(String(36), nullable=False)
    name: Column = Column(String(32))
    running: Column = Column(Boolean)
    action: Column = Column(Integer)
    target_service: Column = Column(String(36))
    target_device: Column = Column(String(36))
    part_owner: Column = Column(String(36))
    running_port : Column = Column(Integer)

    @property
    def serialize(self):
        _ = self.uuid
        mydict = self.__dict__
        #del (mydict['_sa_instance_state'])
        return mydict

    @staticmethod
    def create(user: str, device: str, name: str, running: bool) -> 'Service':
        """
        Creates a new service.
        :param user: The owner's uuid
        :param device: devices uuid
        :param running: service running
        :return: New DeviceModel
        """

        uuid : str = str(uuid4())


        default_port : int = config["services"][name]["default_port"]

        service = Service(uuid=uuid, owner=user, device=device, running=True, name=name, running_port = default_port)

        session.add(service)
        session.commit()

        return service

    def use(self, data):

        if self.name == "Hydra":  # Hydra is the name of an brute force tool for SSH (but now for all services)
            if "target_service" in data and "target_device" in data:
                target_ser: str = data["target_service"]
                target_dev: str = data["target_device"]
            else:
                return None

            self.action : int = int(time.time())
            self.target_service : str  = target_ser
            self.target_device : str = target_dev

            session.commit()

    def public_data(self):
        return {"uuid":self.uuid, "name":self.name, "running_port":self.running_port, "device": self.device}

Base.metadata.create_all(engine)
