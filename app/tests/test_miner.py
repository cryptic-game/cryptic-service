from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.miner import Miner
from models.service import Service
from resources import miner
from schemes import (
    wallet_not_found,
    could_not_start_service,
    success_scheme,
)


class TestMiner(TestCase):
    def setUp(self):
        mock.reset_mocks()

        self.query_miner = mock.MagicMock()
        self.query_service = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {Miner: self.query_miner, Service: self.query_service}.__getitem__

    def test__user_endpoint__miner_get__successful(self):
        mock_service = mock.MagicMock()
        mock_miner = self.query_miner.get.return_value = mock.MagicMock()
        self.assertEqual(mock_miner.serialize, miner.get({}, "", mock_service))
        self.query_miner.get.assert_called_with(mock_service.uuid)

    @patch("resources.miner.check_device_online")
    def test__user_endpoint__miner_list(self, device_online_patch):
        miners = self.query_miner.filter_by.return_value = [mock.MagicMock() for _ in range(5)]
        services = [mock.MagicMock() for _ in range(5)]
        results = services.copy()
        expected_arguments = [m.uuid for m in miners]
        self.query_service.get.side_effect = lambda a: self.assertEqual(expected_arguments.pop(0), a) or results.pop(0)
        online_results = [True, False, True, True, False]
        expected_online_arguments = [s.device for s in services]
        device_online_patch.side_effect = lambda a: self.assertEqual(
            expected_online_arguments.pop(0), a
        ) or online_results.pop(0)
        online_results_copy = online_results.copy()

        expected_result = {
            "miners": [
                {"miner": m.serialize, "service": s.serialize}
                for m, s, e in zip(miners, services, online_results_copy)
                if e
            ]
        }
        actual_result = miner.list_miners({"wallet_uuid": "some-wallet"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_miner.filter_by.assert_called_with(wallet="some-wallet")
        self.assertFalse(results)
        self.assertFalse(online_results)

    @patch("resources.miner.exists_wallet")
    def test__user_endpoint__miner_wallet__wallet_not_found(self, exists_wallet_patch):
        mock_service = mock.MagicMock()
        exists_wallet_patch.return_value = False
        self.assertEqual(wallet_not_found, miner.set_wallet({"wallet_uuid": "wallet"}, "", mock_service))
        exists_wallet_patch.assert_called_with("wallet")

    @patch("resources.miner.get_wallet_owner")
    @patch("resources.miner.update_miner")
    @patch("resources.miner.exists_wallet")
    def test__user_endpoint__miner_wallet__successful(self, exists_wallet_patch, update_miner_patch, owner_patch):
        mock_miner = self.query_miner.get.return_value = mock.MagicMock()
        mock_service = mock.MagicMock()
        exists_wallet_patch.return_value = True
        owners = [mock.MagicMock(), mock.MagicMock()]
        orig_owner = owners.copy()

        def owner_handler(wallet):
            self.assertEqual(mock_miner.wallet, wallet)
            return owners.pop()

        owner_patch.side_effect = owner_handler

        def notification_handler(user, data):
            self.assertEqual(orig_owner.pop(), user)
            if orig_owner:
                self.assertEqual(
                    {"notify-id": "miner-disconnected", "origin": "miner/wallet", "wallet_uuid": mock_miner.wallet},
                    data,
                )
            else:
                self.assertEqual(
                    {"notify-id": "miner-connected", "origin": "miner/wallet", "wallet_uuid": mock_miner.wallet}, data
                )

        mock.m.contact_user.side_effect = notification_handler

        expected_result = mock_miner.serialize
        actual_result = miner.set_wallet({"wallet_uuid": "wallet"}, "", mock_service)

        self.assertEqual(expected_result, actual_result)
        self.query_miner.get.assert_called_with(mock_service.uuid)
        exists_wallet_patch.assert_called_with("wallet")
        update_miner_patch.assert_called_with(mock_miner)
        self.assertEqual("wallet", mock_miner.wallet)
        mock.wrapper.session.commit.assert_called_with()
        self.assertFalse(owners)
        self.assertFalse(orig_owner)

    @patch("resources.miner.exists_wallet")
    def test__user_endpoint__miner_power__wallet_not_found(self, exists_wallet_patch):
        mock_miner = self.query_miner.get.return_value = mock.MagicMock()
        mock_service = mock.MagicMock()
        exists_wallet_patch.return_value = False
        self.assertEqual(wallet_not_found, miner.set_power({}, "", mock_service))
        self.query_miner.get.assert_called_with(mock_service.uuid)
        exists_wallet_patch.assert_called_with(mock_miner.wallet)

    @patch("resources.miner.change_miner_power")
    @patch("resources.miner.update_miner")
    @patch("resources.miner.exists_wallet")
    def test__user_endpoint__miner_power__could_not_start_service(
        self, exists_wallet_patch, update_miner_patch, change_miner_power_patch,
    ):
        mock_miner = self.query_miner.get.return_value = mock.MagicMock()
        mock_service = mock.MagicMock()
        exists_wallet_patch.return_value = True
        change_miner_power_patch.return_value = -1
        self.assertEqual(could_not_start_service, miner.set_power({"power": 42}, "", mock_service))
        self.query_miner.get.assert_called_with(mock_service.uuid)
        exists_wallet_patch.assert_called_with(mock_miner.wallet)
        update_miner_patch.assert_called_with(mock_miner)
        change_miner_power_patch.assert_called_with(42, mock_service.uuid, mock_service.device, mock_service.owner)

    @patch("resources.miner.get_wallet_owner")
    @patch("resources.miner.change_miner_power")
    @patch("resources.miner.update_miner")
    @patch("resources.miner.exists_wallet")
    def test__user_endpoint__miner_power__successful_stopped(
        self, exists_wallet_patch, update_miner_patch, change_miner_power_patch, owner_patch
    ):
        mock_miner = self.query_miner.get.return_value = mock.MagicMock()
        mock_service = mock.MagicMock()
        exists_wallet_patch.return_value = True

        expected_result = mock_miner.serialize
        actual_result = miner.set_power({"power": 0}, "", mock_service)

        self.assertEqual(expected_result, actual_result)
        self.query_miner.get.assert_called_with(mock_service.uuid)
        exists_wallet_patch.assert_called_with(mock_miner.wallet)
        update_miner_patch.assert_called_with(mock_miner)
        change_miner_power_patch.assert_called_with(0, mock_service.uuid, mock_service.device, mock_service.owner)
        self.assertEqual(change_miner_power_patch(), mock_service.speed)
        self.assertEqual(False, mock_service.running)
        self.assertEqual(0, mock_miner.power)
        self.assertEqual(None, mock_miner.started)

        owner_patch.assert_called_with(mock_miner.wallet)
        mock.m.contact_user.assert_called_with(
            owner_patch(),
            {"notify-id": "miner-rate-changed", "origin": "miner/power", "wallet_uuid": mock_miner.wallet},
        )

        mock.wrapper.session.commit.assert_called_with()

    @patch("resources.miner.get_wallet_owner")
    @patch("resources.miner.time.time")
    @patch("resources.miner.change_miner_power")
    @patch("resources.miner.update_miner")
    @patch("resources.miner.exists_wallet")
    def test__user_endpoint__miner_power__successful_started(
        self, exists_wallet_patch, update_miner_patch, change_miner_power_patch, time_patch, owner_patch
    ):
        mock_miner = self.query_miner.get.return_value = mock.MagicMock()
        mock_service = mock.MagicMock()
        exists_wallet_patch.return_value = True
        time_patch.return_value = 1337

        expected_result = mock_miner.serialize
        actual_result = miner.set_power({"power": 42}, "", mock_service)

        self.assertEqual(expected_result, actual_result)
        self.query_miner.get.assert_called_with(mock_service.uuid)
        exists_wallet_patch.assert_called_with(mock_miner.wallet)
        update_miner_patch.assert_called_with(mock_miner)
        change_miner_power_patch.assert_called_with(42, mock_service.uuid, mock_service.device, mock_service.owner)
        self.assertEqual(change_miner_power_patch(), mock_service.speed)
        self.assertEqual(True, mock_service.running)
        self.assertEqual(42, mock_miner.power)
        self.assertEqual(1337000, mock_miner.started)

        owner_patch.assert_called_with(mock_miner.wallet)
        mock.m.contact_user.assert_called_with(
            owner_patch(),
            {"notify-id": "miner-rate-changed", "origin": "miner/power", "wallet_uuid": mock_miner.wallet},
        )

        mock.wrapper.session.commit.assert_called_with()

    @patch("resources.miner.stop_service")
    def test__ms_endpoint__miner_stop(self, stop_service_patch):
        miners = []
        services = []
        service_map = {}
        for i in range(5):
            miners.append(mock.MagicMock())
            service = mock.MagicMock()
            service.running = not i % 2
            service.stop_called = bool(i % 2)
            service.uuid = miners[-1].uuid
            services.append(service)
            service_map[service.uuid] = service

        self.query_miner.filter_by.return_value = miners

        def service_query_handler(uuid):
            m = mock.MagicMock()
            m.first.return_value = service_map[uuid]
            return m

        def stop_service_handler(dev, uuid, user):
            service = service_map[uuid]
            self.assertEqual(service.device, dev)
            self.assertEqual(service.uuid, uuid)
            self.assertEqual(service.owner, user)
            service.stop_called = not service.stop_called

        self.query_service.filter_by.side_effect = service_query_handler
        stop_service_patch.side_effect = stop_service_handler

        self.assertEqual(success_scheme, miner.miner_stop({"wallet_uuid": "my-wallet"}, ""))
        self.query_miner.filter_by.assert_called_with(wallet="my-wallet")

        for service in services:
            self.assertEqual(False, service.running)
            self.assertEqual(True, service.stop_called)

        for m in miners:
            self.assertEqual(None, m.started)

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
