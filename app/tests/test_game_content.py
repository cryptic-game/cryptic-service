from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.service import Service

from resources import game_content
from schemes import invalid_request


class TestGameContent(TestCase):
    def setUp(self):
        mock.reset_mocks()

        self.query_service = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {Service: self.query_service}.__getitem__

    @patch("resources.game_content.config", {"CHANCE": 1337})
    def test__calculate_pos(self):
        self.assertEqual(42 / 1337, game_content.calculate_pos(42))

    def test__portscan__invalid_request(self):
        self.assertEqual(invalid_request, game_content.portscan({}, ""))
        self.assertEqual(invalid_request, game_content.portscan({"target_device": 42}, ""))

    def test__portscan__successful(self):
        def create_service(i):
            s = mock.MagicMock()
            s.running = i % 2 == 0
            s.running_port = i if i % 3 == 0 else None
            return s

        self.query_service.filter_by().all.return_value = services = [create_service(i) for i in range(42)]

        expected_result = {"services": [service.public_data() for service in services[::6]]}
        actual_result = game_content.portscan({"target_device": "the-target"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(device="the-target")
        self.query_service.filter_by().all.assert_called_with()

        for s in services[::6]:
            s.public_data.assert_called_with()

    @patch(
        "resources.game_content.config",
        {"services": {"allowed": {"allow_remote_access": True}, "denied": {"allow_remote_access": False}}},
    )
    def test__part_owner__access_denied(self):
        def create_service(i):
            s = mock.MagicMock()
            s.part_owner = "user" if i % 2 == 0 else "someone-else"
            s.running_port = i if i % 4 == 0 else None
            s.name = "allowed" if i % 8 == 0 else "denied"
            return s

        self.query_service.filter_by().all.return_value = [create_service(i) for i in range(1, 8)]

        self.assertFalse(game_content.part_owner("the-device", "user"))
        self.query_service.filter_by.assert_called_with(device="the-device")
        self.query_service.filter_by().all.assert_called_with()

    @patch(
        "resources.game_content.config",
        {"services": {"allowed": {"allow_remote_access": True}, "denied": {"allow_remote_access": False}}},
    )
    def test__part_owner__access_granted(self):
        def create_service(i):
            s = mock.MagicMock()
            s.part_owner = "user" if i % 2 == 0 else "someone-else"
            s.running_port = i if i % 4 == 0 else None
            s.name = "allowed" if i % 8 == 0 else "denied"
            return s

        self.query_service.filter_by().all.return_value = [create_service(i) for i in range(8)]

        self.assertTrue(game_content.part_owner("the-device", "user"))
        self.query_service.filter_by.assert_called_with(device="the-device")
        self.query_service.filter_by().all.assert_called_with()

    def test__dict2tuple(self):
        expected_result = 2, 3, 5, 7, 11
        actual_result = game_content.dict2tuple({"cpu": 2, "ram": 3, "gpu": 5, "disk": 7, "network": 11})

        self.assertEqual(expected_result, actual_result)
