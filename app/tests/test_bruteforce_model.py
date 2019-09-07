from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.bruteforce import Bruteforce


class TestBruteforceModel(TestCase):
    def setUp(self):
        mock.reset_mocks()

    def test__model__bruteforce__structure(self):
        self.assertEqual("service_bruteforce", Bruteforce.__tablename__)
        self.assertTrue(issubclass(Bruteforce, mock.wrapper.Base))
        for col in ["uuid", "started", "target_service", "target_device", "progress"]:
            self.assertIn(col, dir(Bruteforce))

    def test__model__bruteforce__serialize(self):
        bruteforce = Bruteforce(
            uuid="hydra", started=1234, target_service="ssh-service", target_device="remote-device", progress=13.37
        )

        expected_result = {
            "uuid": "hydra",
            "started": 1234,
            "target_service": "ssh-service",
            "target_device": "remote-device",
            "progress": 13.37,
        }
        serialized = bruteforce.serialize

        self.assertEqual(expected_result, serialized)

        serialized["uuid"] = "something-different"
        self.assertEqual(expected_result, bruteforce.serialize)

    def test__model__bruteforce__create(self):
        actual_result = Bruteforce.create("service-uuid")

        self.assertIsInstance(actual_result, Bruteforce)
        self.assertEqual("service-uuid", actual_result.uuid)
        self.assertEqual(None, actual_result.started)
        self.assertEqual(None, actual_result.target_service)
        self.assertEqual(None, actual_result.target_device)
        self.assertEqual(0, actual_result.progress)
        mock.wrapper.session.add.assert_called_with(actual_result)
        mock.wrapper.session.commit.assert_called_with()

    @patch("models.bruteforce.time.time")
    def test__model__bruteforce__update_progress(self, time_patch):
        time_patch.return_value = 37
        bruteforce = Bruteforce(started=13, progress=4.2)

        bruteforce.update_progress(0.7)

        self.assertEqual(4.2 + (37 - 13) * 0.7, bruteforce.progress)
        self.assertEqual(37, bruteforce.started)
        mock.wrapper.session.commit.assert_called_with()
