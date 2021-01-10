from unittest import TestCase

from mock.mock_loader import mock
from models.service import Service


class TestServiceModel(TestCase):
    def setUp(self):
        mock.reset_mocks()

    def test__model__service__structure(self):
        self.assertEqual("service_service", Service.__tablename__)
        self.assertTrue(issubclass(Service, mock.wrapper.Base))
        for col in ["uuid", "device", "owner", "name", "running", "running_port", "part_owner", "speed"]:
            self.assertIn(col, dir(Service))

    def test__model__service__serialize(self):
        service = Service(
            uuid="service-uuid",
            device="my-device",
            owner="its-me",
            name="ssh",
            running=True,
            running_port=22,
            part_owner="hacker",
            speed=0.7,
        )

        expected_result = {
            "uuid": "service-uuid",
            "device": "my-device",
            "owner": "its-me",
            "name": "ssh",
            "running": True,
            "running_port": 22,
            "part_owner": "hacker",
            "speed": 0.7,
        }
        serialized = service.serialize

        self.assertEqual(expected_result, serialized)

        serialized["uuid"] = "something-different"
        self.assertEqual(expected_result, service.serialize)

    def test__model__service__create(self):
        actual_result = Service.create("service-uuid", "my-device", "its-me", "ssh", 0.7, True)

        self.assertIsInstance(actual_result, Service)
        self.assertEqual("service-uuid", actual_result.uuid)
        self.assertEqual("my-device", actual_result.device)
        self.assertEqual("its-me", actual_result.owner)
        self.assertEqual(True, actual_result.running)
        self.assertEqual("ssh", actual_result.name)
        self.assertEqual(22, actual_result.running_port)
        self.assertEqual(0.7, actual_result.speed)
        mock.wrapper.session.add.assert_called_with(actual_result)
        mock.wrapper.session.commit.assert_called_with()

    def test__model__service__check_access__access_denied(self):
        service = Service(owner="foo", part_owner="bar")

        self.assertFalse(service.check_access("baz"))

    def test__model__service__check_access__is_owner(self):
        service = Service(owner="foo", part_owner="bar")

        self.assertTrue(service.check_access("foo"))

    def test__model__service__check_access__is_part_owner(self):
        service = Service(owner="foo", part_owner="bar")

        self.assertTrue(service.check_access("bar"))

    def test__model__service__public_data(self):
        service = Service()

        expected_result = {
            "uuid": service.uuid,
            "name": service.name,
            "running_port": service.running_port,
            "device": service.device,
        }
        actual_result = service.public_data()

        self.assertEqual(expected_result, actual_result)
