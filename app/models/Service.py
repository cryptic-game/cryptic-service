from objects import db
from uuid import uuid4
import random
import time


class Service(db.Model):
    __tablename__: str = "service"

    uuid: db.Column = db.Column(db.String(32), primary_key=True, unique=True)
    device: db.Column = db.Column(db.String(32), primary_key=True, unique=True)
    owner: db.Column = db.Column(db.String(32), nullable=False)
    name: db.Column = db.Column(db.String(32))
    running: db.Column = db.Column(db.Boolean)
    action: db.Column = db.Column(db.Integer)
    target_service: db.Column = db.Column(db.String(32))
    target_device: db.Column = db.Column(db.String(32))
    part_owner: db.Column = db.Column(db.String(32))

    @property
    def serialize(self):
        _ = self.uuid
        return self.__dict__

    @staticmethod
    def create(user: str, device: str, running: bool) -> 'Service':
        """
        Creates a new service.
        :param user: The owner's uuid
        :param device: devices uuid
        :param running: service running
        :return: New DeviceModel
        """

        uuid = str(uuid4()).replace("-", "")

        service = Service(uuid=uuid, user=user, device=device, running=running)

        db.session.add(service)
        db.session.commit()

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
