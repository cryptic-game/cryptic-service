from objects import session, Base, engine
from uuid import uuid4
import random
import time
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import MetaData


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

    @property
    def serialize(self):
        _ = self.uuid
        mydict = self.__dict__
        del (mydict['_sa_instance_state'])
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

        uuid = str(uuid4()).replace("-", "")

        service = Service(uuid=uuid, owner=user, device=device, running=running, name=name)

        session.add(service)
        session.commit()

        return service

    def use(self, **kwargs):

        if self.name is "Hydra":  # Hydra is the name of an brute force tool for SSH (but now for all services)
            if "target_service" in kwargs and "target_device" in kwargs:
                target_ser: str = kwargs["target_service"]
                target_dev: str = kwargs["target_device"]
            else:
                return None

            self.action = time.time()
            self.target_service = target_ser
            self.target_device = target_dev


Base.metadata.create_all(engine)
