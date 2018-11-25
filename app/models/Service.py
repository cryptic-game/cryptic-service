from objects import db
from uuid import uuid4
import random


class Service(db.Model):
    __tablename__: str = "services"
    uuid: db.Column = db.Column(db.String(32), primary_key=True, unique=True)
    device: db.Column = db.Column(db.String(32), primary_key=True, unique=True)
    owner: db.Column = db.Column(db.String(32), nullable=False)
    name: db.Column = db.Column(db.String(32))
    running: db.Column = db.Column(db.Boolean)

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
