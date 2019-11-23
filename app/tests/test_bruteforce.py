from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.bruteforce import Bruteforce
from models.service import Service
from resources import bruteforce
from schemes import (
    service_not_found,
    service_not_running,
    attack_already_running,
    success_scheme,
    attack_not_running,
    could_not_start_service,
)


class TestBruteforce(TestCase):
    def setUp(self):
        mock.reset_mocks()

        self.query_service = mock.MagicMock()
        self.query_bruteforce = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {
            Service: self.query_service,
            Bruteforce: self.query_bruteforce,
        }.__getitem__

    def test__user_endpoint__bruteforce_attack__attack_already_running(self):
        mock_service = mock.MagicMock()
        mock_service.running = True
        self.assertEqual(attack_already_running, bruteforce.attack({}, "", mock_service))

    def test__user_endpoint__bruteforce_attack__target_service_not_found(self):
        mock_service = mock.MagicMock()
        mock_service.running = False
        self.query_service.filter_by().first.return_value = None

        expected_result = service_not_found
        actual_result = bruteforce.attack(
            {"target_device": "victim-device", "target_service": "ssh-or-telnet"}, "", mock_service
        )

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid="ssh-or-telnet", device="victim-device")

    def test__user_endpoint__bruteforce_attack__target_service_not_running(self):
        mock_service = mock.MagicMock()
        mock_service.running = False
        mock_target_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_target_service.running = False

        expected_result = service_not_running
        actual_result = bruteforce.attack(
            {"target_device": "victim-device", "target_service": "ssh-or-telnet"}, "", mock_service
        )

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid="ssh-or-telnet", device="victim-device")

    @patch("resources.bruteforce.register_service")
    def test__user_endpoint__bruteforce_attack__could_not_start_service(self, register_patch):
        mock_target_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_target_service.running = True
        mock_service = mock.MagicMock()
        mock_service.running = False
        register_patch.return_value = -1

        expected_result = could_not_start_service
        actual_result = bruteforce.attack(
            {"target_device": "victim-device", "target_service": "ssh-or-telnet"}, "", mock_service
        )

        self.assertEqual(expected_result, actual_result)
        register_patch.assert_called_with(mock_service.device, mock_service.uuid, mock_service.name, mock_service.owner)
        self.query_service.filter_by.assert_called_with(uuid="ssh-or-telnet", device="victim-device")

    @patch("resources.bruteforce.time")
    @patch("resources.bruteforce.register_service")
    def test__user_endpoint__bruteforce_attack__successful(self, register_patch, time_patch):
        time_patch.time.return_value = "1337"
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_bruteforce.uuid = "bruteforce-service"
        mock_target_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_target_service.running = True
        mock_service = mock.MagicMock()
        mock_service.running = False

        expected_result = success_scheme
        actual_result = bruteforce.attack(
            {"target_device": "victim-device", "target_service": "ssh-or-telnet"}, "user", mock_service,
        )

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid="ssh-or-telnet", device="victim-device")
        self.query_bruteforce.get.assert_called_with(mock_service.uuid)
        self.assertEqual("ssh-or-telnet", mock_bruteforce.target_service)
        self.assertEqual("victim-device", mock_bruteforce.target_device)
        self.assertEqual(1337, mock_bruteforce.started)
        self.assertEqual(0, mock_bruteforce.progress)
        register_patch.assert_called_with(mock_service.device, mock_service.uuid, mock_service.name, mock_service.owner)
        self.assertEqual(mock_service.speed, register_patch())
        self.assertEqual(True, mock_service.running)
        mock.wrapper.session.commit.assert_called_with()

    def test__user_endpoint__bruteforce_status__attack_not_running(self):
        mock_service = self.query_service.get.return_value = mock.MagicMock()
        mock_service.running = False
        self.assertEqual(attack_not_running, bruteforce.status({}, "", mock_service))

    def test__user_endpoint__bruteforce_status__successful(self):
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_bruteforce.serialize = {"foo": "bar", "foo2": "bar2"}
        mock_service = self.query_service.get.return_value = mock.MagicMock()
        mock_service.running = True

        expected_result = {"foo": "bar", "foo2": "bar2"}
        actual_result = bruteforce.status({"service_uuid": "hydra"}, "", mock_service)

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.get.assert_called_with(mock_service.uuid)
        mock_bruteforce.update_progress.assert_called_with(mock_service.speed)

    def test__user_endpoint__bruteforce_stop__attack_not_running(self):
        mock_service = self.query_service.get.return_value = mock.MagicMock()
        mock_service.running = False
        self.assertEqual(attack_not_running, bruteforce.stop({"service_uuid": "hydra"}, "user", mock_service))

    @patch("resources.bruteforce.stop_service")
    def test__user_endpoint__bruteforce_stop__target_service_not_found(self, stop_service_patch):
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_service = mock.MagicMock()
        mock_service.running = True
        self.query_service.filter_by().first.return_value = None
        old_target_device = mock_bruteforce.target_device
        old_target_service = mock_bruteforce.target_service

        expected_result = service_not_found
        actual_result = bruteforce.stop({}, "user", mock_service)

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.get.assert_called_with(mock_service.uuid)
        self.query_service.filter_by.assert_called_with(uuid=old_target_service, device=old_target_device)
        mock_bruteforce.update_progress.assert_called_with(mock_service.speed)
        self.assertEqual(None, mock_bruteforce.target_device)
        self.assertEqual(None, mock_bruteforce.target_service)
        self.assertEqual(None, mock_bruteforce.started)
        self.assertEqual(0, mock_bruteforce.progress)
        self.assertEqual(False, mock_service.running)
        mock.wrapper.session.commit.assert_called_with()
        stop_service_patch.assert_called_with(mock_service.device, mock_service.uuid, mock_service.owner)

    @patch("resources.bruteforce.stop_service")
    def test__user_endpoint__bruteforce_stop__target_service_not_running(self, stop_service_patch):
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_service = mock.MagicMock()
        mock_service.running = True
        mock_target_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_target_service.running = False
        old_target_device = mock_bruteforce.target_device
        old_target_service = mock_bruteforce.target_service

        expected_result = service_not_running
        actual_result = bruteforce.stop({}, "user", mock_service)

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.get.assert_called_with(mock_service.uuid)
        self.query_service.filter_by.assert_called_with(uuid=old_target_service, device=old_target_device)
        mock_bruteforce.update_progress.assert_called_with(mock_service.speed)
        self.assertEqual(None, mock_bruteforce.target_device)
        self.assertEqual(None, mock_bruteforce.target_service)
        self.assertEqual(None, mock_bruteforce.started)
        self.assertEqual(0, mock_bruteforce.progress)
        self.assertEqual(False, mock_service.running)
        mock.wrapper.session.commit.assert_called_with()
        stop_service_patch.assert_called_with(mock_service.device, mock_service.uuid, mock_service.owner)

    @patch("resources.bruteforce.calculate_pos")
    @patch("resources.bruteforce.stop_service")
    def test__user_endpoint__bruteforce_stop__successful_but_no_access(self, stop_service_patch, calculate_pos_patch):
        calculate_pos_patch.return_value = 0
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_service = mock.MagicMock()
        mock_service.running = True
        mock_target_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_target_service.running = True
        old_progress = mock_bruteforce.progress
        old_target_device = mock_bruteforce.target_device
        old_target_service = mock_bruteforce.target_service
        old_part_owner = mock_target_service.part_owner

        expected_result = {"ok": True, "access": False, "progress": old_progress, "target_device": old_target_device}
        actual_result = bruteforce.stop({}, "user", mock_service)

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.get.assert_called_with(mock_service.uuid)
        self.query_service.filter_by.assert_called_with(uuid=old_target_service, device=old_target_device)
        mock_bruteforce.update_progress.assert_called_with(mock_service.speed)
        self.assertEqual(None, mock_bruteforce.target_device)
        self.assertEqual(None, mock_bruteforce.target_service)
        self.assertEqual(None, mock_bruteforce.started)
        self.assertEqual(0, mock_bruteforce.progress)
        self.assertEqual(False, mock_service.running)
        mock.wrapper.session.commit.assert_called_with()
        stop_service_patch.assert_called_with(mock_service.device, mock_service.uuid, mock_service.owner)
        self.assertEqual(old_part_owner, mock_target_service.part_owner)

    @patch("resources.bruteforce.calculate_pos")
    @patch("resources.bruteforce.stop_service")
    def test__user_endpoint__bruteforce_stop__successful_got_access(self, stop_service_patch, calculate_pos_patch):
        calculate_pos_patch.return_value = 2
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_service = mock.MagicMock()
        mock_service.running = True
        mock_target_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_target_service.running = True
        old_progress = mock_bruteforce.progress
        old_target_device = mock_bruteforce.target_device
        old_target_service = mock_bruteforce.target_service

        expected_result = {"ok": True, "access": True, "progress": old_progress, "target_device": old_target_device}
        actual_result = bruteforce.stop({}, "user", mock_service)

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.get.assert_called_with(mock_service.uuid)
        self.query_service.filter_by.assert_called_with(uuid=old_target_service, device=old_target_device)
        mock_bruteforce.update_progress.assert_called_with(mock_service.speed)
        self.assertEqual(None, mock_bruteforce.target_device)
        self.assertEqual(None, mock_bruteforce.target_service)
        self.assertEqual(None, mock_bruteforce.started)
        self.assertEqual(0, mock_bruteforce.progress)
        self.assertEqual(False, mock_service.running)
        mock.wrapper.session.commit.assert_called_with()
        stop_service_patch.assert_called_with(mock_service.device, mock_service.uuid, mock_service.owner)
        self.assertEqual("user", mock_target_service.part_owner)
