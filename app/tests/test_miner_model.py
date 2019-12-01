from unittest import TestCase
from unittest.mock import _patch, patch

from mock.mock_loader import mock
from models.miner import Miner
from models.service import Service


class TestMinerModel(TestCase):
    def setUp(self):
        mock.reset_mocks()

        self.query_service = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {Service: self.query_service}.__getitem__

    def test__model__miner__structure(self):
        self.assertEqual("service_miner", Miner.__tablename__)
        self.assertTrue(issubclass(Miner, mock.wrapper.Base))
        for col in ["uuid", "wallet", "started", "power"]:
            self.assertIn(col, dir(Miner))

    def test__model__miner__serialize(self):
        miner = Miner(uuid="my-miner", wallet="some-wallet", started=1337, power=0.83)

        expected_result = {"uuid": "my-miner", "wallet": "some-wallet", "started": 1337, "power": 0.83}
        serialized = miner.serialize

        self.assertEqual(expected_result, serialized)

        serialized["uuid"] = "something-different"
        self.assertEqual(expected_result, miner.serialize)

    def test__model__miner__create(self):
        actual_result = Miner.create("my-miner", "some-wallet")

        self.assertIsInstance(actual_result, Miner)
        self.assertEqual("my-miner", actual_result.uuid)
        self.assertEqual("some-wallet", actual_result.wallet)
        self.assertEqual(None, actual_result.started)
        self.assertEqual(0, actual_result.power)

    def test__model__miner__update_miner__not_running(self):
        miner = Miner()
        service = Service(running=False)
        self.query_service.get.return_value = service

        self.assertEqual(0, miner.update_miner())
        self.query_service.get.assert_called_with(miner.uuid)

    @patch("models.miner.time.time")
    def test__model__miner__update_miner__successful(self, time_patch):
        miner = Miner(started=13)
        service = Service(running=True, speed=0.8)
        self.query_service.get.return_value = service
        time_patch.return_value = 37

        expected_result = int((37000 - 13) * 0.8)
        actual_result = miner.update_miner()

        self.assertEqual(expected_result, actual_result)
        self.assertEqual(37000, miner.started)
        mock.wrapper.session.commit.assert_called_with()
