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

    def test__user_endpoint__bruteforce_attack__bruteforce_service_not_found(self):
        self.query_service.filter_by().first.return_value = mock.MagicMock()
        self.query_bruteforce.filter_by().first.return_value = None

        expected_result = service_not_found
        actual_result = bruteforce.attack(
            {
                "device_uuid": "attacker-device",
                "service_uuid": "bruteforce-service",
                "target_device": "victim-device",
                "target_service": "ssh-or-telnet",
            },
            "user",
        )

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.filter_by.assert_called_with(uuid="bruteforce-service")
        self.query_service.filter_by.assert_called_with(uuid="ssh-or-telnet", device="victim-device")

    def test__user_endpoint__bruteforce_attack__target_service_not_found(self):
        self.query_service.filter_by().first.return_value = None
        self.query_bruteforce.filter_by().first.return_value = mock.MagicMock()

        expected_result = service_not_found
        actual_result = bruteforce.attack(
            {
                "device_uuid": "attacker-device",
                "service_uuid": "bruteforce-service",
                "target_device": "victim-device",
                "target_service": "ssh-or-telnet",
            },
            "user",
        )

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.filter_by.assert_called_with(uuid="bruteforce-service")
        self.query_service.filter_by.assert_called_with(uuid="ssh-or-telnet", device="victim-device")

    def test__user_endpoint__bruteforce_attack__target_service_not_running(self):
        mock_target_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_target_service.running = False
        self.query_bruteforce.filter_by().first.return_value = mock.MagicMock()

        expected_result = service_not_running
        actual_result = bruteforce.attack(
            {
                "device_uuid": "attacker-device",
                "service_uuid": "bruteforce-service",
                "target_device": "victim-device",
                "target_service": "ssh-or-telnet",
            },
            "user",
        )

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.filter_by.assert_called_with(uuid="bruteforce-service")
        self.query_service.filter_by.assert_called_with(uuid="ssh-or-telnet", device="victim-device")

    def test__user_endpoint__bruteforce_attack__attack_already_running(self):
        mock_bruteforce = self.query_bruteforce.filter_by().first.return_value = mock.MagicMock()
        mock_bruteforce.uuid = "bruteforce-service"
        mock_target_service = mock.MagicMock()
        mock_target_service.running = True
        mock_own_service = mock.MagicMock()
        mock_own_service.running = True
        expected_params = [{"uuid": "ssh-or-telnet", "device": "victim-device"}, {"uuid": "bruteforce-service"}]
        return_values = [mock_target_service, mock_own_service]

        def filter_by_handler(**kwargs):
            self.assertEqual(expected_params.pop(0), kwargs)
            out = mock.MagicMock()
            out.first.return_value = return_values.pop(0)
            return out

        self.query_service.filter_by.side_effect = filter_by_handler

        expected_result = attack_already_running
        actual_result = bruteforce.attack(
            {
                "device_uuid": "attacker-device",
                "service_uuid": "bruteforce-service",
                "target_device": "victim-device",
                "target_service": "ssh-or-telnet",
            },
            "user",
        )

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.filter_by.assert_called_with(uuid="bruteforce-service")

    @patch("resources.bruteforce.register_service")
    def test__user_endpoint__bruteforce_attack__could_not_start_service(self, register_patch):
        mock_bruteforce = self.query_bruteforce.filter_by().first.return_value = mock.MagicMock()
        mock_bruteforce.uuid = "bruteforce-service"
        mock_target_service = mock.MagicMock()
        mock_target_service.running = True
        mock_own_service = mock.MagicMock()
        mock_own_service.running = False
        expected_params = [{"uuid": "ssh-or-telnet", "device": "victim-device"}, {"uuid": "bruteforce-service"}]
        return_values = [mock_target_service, mock_own_service]
        register_patch.return_value = -1

        def filter_by_handler(**kwargs):
            self.assertEqual(expected_params.pop(0), kwargs)
            out = mock.MagicMock()
            out.first.return_value = return_values.pop(0)
            return out

        self.query_service.filter_by.side_effect = filter_by_handler

        expected_result = could_not_start_service
        actual_result = bruteforce.attack(
            {
                "device_uuid": "attacker-device",
                "service_uuid": "bruteforce-service",
                "target_device": "victim-device",
                "target_service": "ssh-or-telnet",
            },
            "user",
        )

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.filter_by.assert_called_with(uuid="bruteforce-service")
        register_patch.assert_called_with(
            mock_own_service.device, mock_own_service.uuid, mock_own_service.name, mock_own_service.owner
        )

    @patch("resources.bruteforce.time")
    @patch("resources.bruteforce.register_service")
    def test__user_endpoint__bruteforce_attack__successful(self, register_patch, time_patch):
        time_patch.time.return_value = "1337"
        mock_bruteforce = self.query_bruteforce.filter_by().first.return_value = mock.MagicMock()
        mock_bruteforce.uuid = "bruteforce-service"
        mock_target_service = mock.MagicMock()
        mock_target_service.running = True
        mock_own_service = mock.MagicMock()
        mock_own_service.running = False
        expected_params = [{"uuid": "ssh-or-telnet", "device": "victim-device"}, {"uuid": "bruteforce-service"}]
        return_values = [mock_target_service, mock_own_service]

        def filter_by_handler(**kwargs):
            self.assertEqual(expected_params.pop(0), kwargs)
            out = mock.MagicMock()
            out.first.return_value = return_values.pop(0)
            return out

        self.query_service.filter_by.side_effect = filter_by_handler

        expected_result = success_scheme
        actual_result = bruteforce.attack(
            {
                "device_uuid": "attacker-device",
                "service_uuid": "bruteforce-service",
                "target_device": "victim-device",
                "target_service": "ssh-or-telnet",
            },
            "user",
        )

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.filter_by.assert_called_with(uuid="bruteforce-service")
        self.assertEqual("ssh-or-telnet", mock_bruteforce.target_service)
        self.assertEqual("victim-device", mock_bruteforce.target_device)
        self.assertEqual(1337, mock_bruteforce.started)
        self.assertEqual(0, mock_bruteforce.progress)
        register_patch.assert_called_with(
            mock_own_service.device, mock_own_service.uuid, mock_own_service.name, mock_own_service.owner
        )
        self.assertEqual(mock_own_service.speed, register_patch())
        self.assertEqual(True, mock_own_service.running)
        mock.wrapper.session.commit.assert_called_with()

    def test__user_endpoint__bruteforce_status__service_not_found(self):
        self.query_bruteforce.get.return_value = None
        self.assertEqual(service_not_found, bruteforce.status({"device_uuid": "dev", "service_uuid": "hydra"}, ""))
        self.query_bruteforce.get.assert_called_with("hydra")

    def test__user_endpoint__bruteforce_status__attack_not_running(self):
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_service = self.query_service.get.return_value = mock.MagicMock()
        mock_service.running = False
        self.assertEqual(attack_not_running, bruteforce.status({"device_uuid": "dev", "service_uuid": "hydra"}, ""))
        self.query_bruteforce.get.assert_called_with("hydra")
        self.query_service.get.assert_called_with(mock_bruteforce.uuid)

    def test__user_endpoint__bruteforce_status__successful(self):
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_bruteforce.serialize = {"foo": "bar", "foo2": "bar2"}
        mock_service = self.query_service.get.return_value = mock.MagicMock()
        mock_service.running = True

        expected_result = {"foo": "bar", "foo2": "bar2", "progress": mock_bruteforce.progress}
        actual_result = bruteforce.status({"device_uuid": "dev", "service_uuid": "hydra"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.get.assert_called_with("hydra")
        self.query_service.get.assert_called_with(mock_bruteforce.uuid)
        mock_bruteforce.update_progress.assert_called_with(mock_service.speed)

    def test__user_endpoint__bruteforce_stop__bruteforce_service_not_found(self):
        self.query_bruteforce.get.return_value = None
        self.assertEqual(service_not_found, bruteforce.stop({"service_uuid": "hydra"}, "user"))
        self.query_bruteforce.get.assert_called_with("hydra")

    def test__user_endpoint__bruteforce_stop__attack_not_running(self):
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_own_service = self.query_service.get.return_value = mock.MagicMock()
        mock_own_service.running = False
        self.assertEqual(attack_not_running, bruteforce.stop({"service_uuid": "hydra"}, "user"))
        self.query_bruteforce.get.assert_called_with("hydra")
        self.query_service.get.assert_called_with(mock_bruteforce.uuid)

    def test__user_endpoint__bruteforce_stop__target_service_not_found(self):
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_own_service = self.query_service.get.return_value = mock.MagicMock()
        mock_own_service.running = True
        self.query_service.filter_by().first.return_value = None
        self.assertEqual(service_not_found, bruteforce.stop({"service_uuid": "hydra"}, "user"))
        self.query_bruteforce.get.assert_called_with("hydra")
        self.query_service.get.assert_called_with(mock_bruteforce.uuid)
        self.query_service.filter_by.assert_called_with(
            uuid=mock_bruteforce.target_service, device=mock_bruteforce.target_device
        )

    @patch("resources.bruteforce.calculate_pos")
    @patch("resources.bruteforce.stop_service")
    def test__user_endpoint__bruteforce_stop__successful_but_no_access(self, stop_service_patch, calc_patch):
        calc_patch.return_value = 0
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_own_service = self.query_service.get.return_value = mock.MagicMock()
        mock_own_service.running = True
        mock_target_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        old_progress = mock_bruteforce.progress
        old_target_service = mock_bruteforce.target_service
        old_target_device = mock_bruteforce.target_device
        old_part_owner = mock_target_service.part_owner

        expected_result = {
            "ok": True,
            "access": False,
            "progress": old_progress,
            "target_device": mock_bruteforce.target_device,
        }
        actual_result = bruteforce.stop({"service_uuid": "hydra"}, "user")

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.get.assert_called_with("hydra")
        self.query_service.get.assert_called_with(mock_bruteforce.uuid)
        self.query_service.filter_by.assert_called_with(uuid=old_target_service, device=old_target_device)
        mock_bruteforce.update_progress.assert_called_with(mock_own_service.speed)
        self.assertEqual(None, mock_bruteforce.target_device)
        self.assertEqual(None, mock_bruteforce.target_service)
        self.assertEqual(None, mock_bruteforce.started)
        self.assertEqual(0, mock_bruteforce.progress)
        self.assertEqual(False, mock_own_service.running)
        mock.wrapper.session.commit.assert_called_with()
        stop_service_patch.assert_called_with(mock_own_service.device, mock_own_service.uuid, mock_own_service.owner)
        self.assertEqual(old_part_owner, mock_target_service.part_owner)

    @patch("resources.bruteforce.calculate_pos")
    @patch("resources.bruteforce.stop_service")
    def test__user_endpoint__bruteforce_stop__successful_got_access(self, stop_service_patch, calc_patch):
        calc_patch.return_value = 2
        mock_bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()
        mock_own_service = self.query_service.get.return_value = mock.MagicMock()
        mock_own_service.running = True
        mock_target_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        old_progress = mock_bruteforce.progress
        old_target_service = mock_bruteforce.target_service
        old_target_device = mock_bruteforce.target_device

        expected_result = {
            "ok": True,
            "access": True,
            "progress": old_progress,
            "target_device": mock_bruteforce.target_device,
        }
        actual_result = bruteforce.stop({"service_uuid": "hydra"}, "user")

        self.assertEqual(expected_result, actual_result)
        self.query_bruteforce.get.assert_called_with("hydra")
        self.query_service.get.assert_called_with(mock_bruteforce.uuid)
        self.query_service.filter_by.assert_called_with(uuid=old_target_service, device=old_target_device)
        mock_bruteforce.update_progress.assert_called_with(mock_own_service.speed)
        self.assertEqual(None, mock_bruteforce.target_device)
        self.assertEqual(None, mock_bruteforce.target_service)
        self.assertEqual(None, mock_bruteforce.started)
        self.assertEqual(0, mock_bruteforce.progress)
        self.assertEqual(False, mock_own_service.running)
        mock.wrapper.session.commit.assert_called_with()
        stop_service_patch.assert_called_with(mock_own_service.device, mock_own_service.uuid, mock_own_service.owner)
        self.assertEqual("user", mock_target_service.part_owner)
