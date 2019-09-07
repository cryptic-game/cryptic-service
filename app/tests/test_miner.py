from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.miner import Miner
from models.service import Service
from resources import miner
from schemes import miner_not_found, device_not_found, permission_denied, wallet_not_found


class TestMiner(TestCase):
    def setUp(self):
        mock.reset_mocks()

        self.query_miner = mock.MagicMock()
        self.query_service = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {Miner: self.query_miner, Service: self.query_service}.__getitem__

    def test__user_endpoint__miner_get__miner_not_found(self):
        self.query_miner.filter_by().first.return_value = None
        self.assertEqual(miner_not_found, miner.get({"service_uuid": "my-miner"}, ""))
        self.query_miner.filter_by.assert_called_with(uuid="my-miner")

    def test__user_endpoint__miner_get__successful(self):
        mock_miner = self.query_miner.filter_by().first.return_value = mock.MagicMock()
        self.assertEqual(mock_miner.serialize, miner.get({"service_uuid": "my-miner"}, ""))
        self.query_miner.filter_by.assert_called_with(uuid="my-miner")

    def test__user_endpoint__miner_list(self):
        miners = self.query_miner.filter_by.return_value = [mock.MagicMock() for _ in range(5)]

        expected_result = {"miners": [m.serialize for m in miners]}
        actual_result = miner.list_miners({"wallet_uuid": "some-wallet"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_miner.filter_by.assert_called_with(wallet="some-wallet")

    def test__user_endpoint__miner_wallet__miner_not_found(self):
        self.query_miner.filter_by().first.return_value = None
        self.assertEqual(miner_not_found, miner.set_wallet({"service_uuid": "miner", "wallet_uuid": "wallet"}, ""))
        self.query_miner.filter_by.assert_called_with(uuid="miner")

    @patch("resources.miner.exists_device")
    def test__user_endpoint__miner_wallet__device_not_found(self, exists_device_patch):
        self.query_miner.filter_by().first.return_value = mock.MagicMock()
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        exists_device_patch.return_value = False
        self.assertEqual(device_not_found, miner.set_wallet({"service_uuid": "miner", "wallet_uuid": "wallet"}, ""))
        self.query_miner.filter_by.assert_called_with(uuid="miner")
        self.query_service.filter_by.assert_called_with(uuid="miner")
        exists_device_patch.assert_called_with(mock_service.device)

    @patch("resources.miner.controls_device")
    @patch("resources.miner.exists_device")
    def test__user_endpoint__miner_wallet__permission_denied(self, exists_device_patch, controls_device_patch):
        self.query_miner.filter_by().first.return_value = mock.MagicMock()
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        exists_device_patch.return_value = True
        controls_device_patch.return_value = False
        self.assertEqual(permission_denied, miner.set_wallet({"service_uuid": "miner", "wallet_uuid": "wallet"}, "u"))
        self.query_miner.filter_by.assert_called_with(uuid="miner")
        self.query_service.filter_by.assert_called_with(uuid="miner")
        exists_device_patch.assert_called_with(mock_service.device)
        controls_device_patch.assert_called_with(mock_service.device, "u")

    @patch("resources.miner.exists_wallet")
    @patch("resources.miner.controls_device")
    @patch("resources.miner.exists_device")
    def test__user_endpoint__miner_wallet__wallet_not_found(
        self, exists_device_patch, controls_device_patch, exists_wallet_patch
    ):
        self.query_miner.filter_by().first.return_value = mock.MagicMock()
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        exists_device_patch.return_value = True
        controls_device_patch.return_value = True
        exists_wallet_patch.return_value = False
        self.assertEqual(wallet_not_found, miner.set_wallet({"service_uuid": "miner", "wallet_uuid": "wallet"}, "u"))
        self.query_miner.filter_by.assert_called_with(uuid="miner")
        self.query_service.filter_by.assert_called_with(uuid="miner")
        exists_device_patch.assert_called_with(mock_service.device)
        controls_device_patch.assert_called_with(mock_service.device, "u")
        exists_wallet_patch.assert_called_with("wallet")

    @patch("resources.miner.update_miner")
    @patch("resources.miner.exists_wallet")
    @patch("resources.miner.controls_device")
    @patch("resources.miner.exists_device")
    def test__user_endpoint__miner_wallet__successful(
        self, exists_device_patch, controls_device_patch, exists_wallet_patch, update_miner_patch
    ):
        mock_miner = self.query_miner.filter_by().first.return_value = mock.MagicMock()
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        exists_device_patch.return_value = True
        controls_device_patch.return_value = True
        exists_wallet_patch.return_value = True

        expected_result = mock_miner.serialize
        actual_result = miner.set_wallet({"service_uuid": "miner", "wallet_uuid": "wallet"}, "u")

        self.assertEqual(expected_result, actual_result)
        self.query_miner.filter_by.assert_called_with(uuid="miner")
        self.query_service.filter_by.assert_called_with(uuid="miner")
        exists_device_patch.assert_called_with(mock_service.device)
        controls_device_patch.assert_called_with(mock_service.device, "u")
        exists_wallet_patch.assert_called_with("wallet")
        update_miner_patch.assert_called_with(mock_miner)
        self.assertEqual("wallet", mock_miner.wallet)
        mock.wrapper.session.commit.assert_called_with()

    def test__user_endpoint__miner_power__miner_not_found(self):
        self.query_miner.filter_by().first.return_value = None
        self.assertEqual(miner_not_found, miner.set_power({"service_uuid": "miner", "power": 42}, ""))
        self.query_miner.filter_by.assert_called_with(uuid="miner")

    @patch("resources.miner.exists_device")
    def test__user_endpoint__miner_power__device_not_found(self, exists_device_patch):
        self.query_miner.filter_by().first.return_value = mock.MagicMock()
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        exists_device_patch.return_value = False
        self.assertEqual(device_not_found, miner.set_power({"service_uuid": "miner", "power": 42}, ""))
        self.query_miner.filter_by.assert_called_with(uuid="miner")
        self.query_service.filter_by.assert_called_with(uuid="miner")
        exists_device_patch.assert_called_with(mock_service.device)

    @patch("resources.miner.controls_device")
    @patch("resources.miner.exists_device")
    def test__user_endpoint__miner_power__permission_denied(self, exists_device_patch, controls_device_patch):
        self.query_miner.filter_by().first.return_value = mock.MagicMock()
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        exists_device_patch.return_value = True
        controls_device_patch.return_value = False
        self.assertEqual(permission_denied, miner.set_power({"service_uuid": "miner", "power": 42}, "u"))
        self.query_miner.filter_by.assert_called_with(uuid="miner")
        self.query_service.filter_by.assert_called_with(uuid="miner")
        exists_device_patch.assert_called_with(mock_service.device)
        controls_device_patch.assert_called_with(mock_service.device, "u")

    @patch("resources.miner.change_miner_power")
    @patch("resources.miner.update_miner")
    @patch("resources.miner.controls_device")
    @patch("resources.miner.exists_device")
    def test__user_endpoint__miner_power__successful_stopped(
        self, exists_device_patch, controls_device_patch, update_miner_patch, change_miner_power_patch
    ):
        mock_miner = self.query_miner.filter_by().first.return_value = mock.MagicMock()
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        exists_device_patch.return_value = True
        controls_device_patch.return_value = True

        expected_result = mock_miner.serialize
        actual_result = miner.set_power({"service_uuid": "miner", "power": 0}, "u")

        self.assertEqual(expected_result, actual_result)
        self.query_miner.filter_by.assert_called_with(uuid="miner")
        self.query_service.filter_by.assert_called_with(uuid="miner")
        exists_device_patch.assert_called_with(mock_service.device)
        controls_device_patch.assert_called_with(mock_service.device, "u")
        update_miner_patch.assert_called_with(mock_miner)
        change_miner_power_patch.assert_called_with(0, "miner", mock_service.device, mock_service.owner)
        self.assertEqual(change_miner_power_patch(), mock_service.speed)
        self.assertEqual(False, mock_service.running)
        self.assertEqual(0, mock_miner.power)
        self.assertEqual(None, mock_miner.started)
        mock.wrapper.session.commit.assert_called_with()

    @patch("resources.miner.time.time")
    @patch("resources.miner.change_miner_power")
    @patch("resources.miner.update_miner")
    @patch("resources.miner.controls_device")
    @patch("resources.miner.exists_device")
    def test__user_endpoint__miner_power__successful_started(
        self, exists_device_patch, controls_device_patch, update_miner_patch, change_miner_power_patch, time_patch
    ):
        mock_miner = self.query_miner.filter_by().first.return_value = mock.MagicMock()
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        exists_device_patch.return_value = True
        controls_device_patch.return_value = True
        time_patch.return_value = "1337"

        expected_result = mock_miner.serialize
        actual_result = miner.set_power({"service_uuid": "miner", "power": 42}, "u")

        self.assertEqual(expected_result, actual_result)
        self.query_miner.filter_by.assert_called_with(uuid="miner")
        self.query_service.filter_by.assert_called_with(uuid="miner")
        exists_device_patch.assert_called_with(mock_service.device)
        controls_device_patch.assert_called_with(mock_service.device, "u")
        update_miner_patch.assert_called_with(mock_miner)
        change_miner_power_patch.assert_called_with(42, "miner", mock_service.device, mock_service.owner)
        self.assertEqual(change_miner_power_patch(), mock_service.speed)
        self.assertEqual(True, mock_service.running)
        self.assertEqual(42, mock_miner.power)
        self.assertEqual(1337, mock_miner.started)
        mock.wrapper.session.commit.assert_called_with()

    def test__ms_endpoint__miner_collect(self):
        def make_miner(coins):
            out = mock.MagicMock()
            out.update_miner.return_value = coins
            return out

        miners = self.query_miner.filter_by.return_value = [make_miner(i * 3 + 2) for i in range(5)]

        expected_result = {"coins": 40}
        actual_result = miner.collect({"wallet_uuid": "wallet"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_miner.filter_by.assert_called_with(wallet="wallet")
        for m in miners:
            m.update_miner.assert_called_with()
