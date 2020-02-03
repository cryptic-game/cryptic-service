from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.bruteforce import Bruteforce
from models.miner import Miner
from models.service import Service
from resources import essentials
from schemes import invalid_request, wallet_not_found


class TestEssentials(TestCase):
    def setUp(self):
        mock.reset_mocks()

        self.query_bruteforce = mock.MagicMock()
        self.query_miner = mock.MagicMock()
        self.query_service = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {
            Service: self.query_service,
            Bruteforce: self.query_bruteforce,
            Miner: self.query_miner,
        }.__getitem__

    def test__exists_device(self):
        device = mock.MagicMock()
        expected_result = mock.MagicMock()
        mock.m.contact_microservice.return_value = {"exist": expected_result}

        actual_result = essentials.exists_device(device)

        self.assertEqual(expected_result, actual_result)
        mock.m.contact_microservice.assert_called_with("device", ["exist"], {"device_uuid": device})

    @patch(
        "resources.essentials.config",
        {
            "services": {
                "miner": {
                    "needs": {"cpu": 2, "ram": 3, "gpu": 5, "disk": 7, "network": 11},
                    "speedm": lambda *args, **kwargs: (args, kwargs),
                }
            }
        },
    )
    @patch("resources.essentials.stop_service")
    def test__change_miner_power__could_not_start_service(self, stop_service_patch):
        mock.m.contact_microservice.return_value = {"error": "some-error"}

        expected_result = -1
        actual_result = essentials.change_miner_power(0.8, "the-miner", "my-device", "user")

        self.assertEqual(expected_result, actual_result)
        stop_service_patch.assert_called_with("my-device", "the-miner", "user")
        mock.m.contact_microservice.assert_called_with(
            "device",
            ["hardware", "register"],
            {
                "user": "user",
                "service_uuid": "the-miner",
                "device_uuid": "my-device",
                "cpu": 2 * 0.8,
                "ram": 3 * 0.8,
                "gpu": 5 * 0.8,
                "disk": 7 * 0.8,
                "network": 11 * 0.8,
            },
        )

    @patch("resources.essentials.game_content.dict2tuple")
    @patch(
        "resources.essentials.config",
        {
            "services": {
                "miner": {
                    "needs": {"cpu": 2, "ram": 3, "gpu": 5, "disk": 7, "network": 11},
                    "speedm": lambda *args, **kwargs: (args, kwargs),
                }
            }
        },
    )
    @patch("resources.essentials.stop_service")
    def test__change_miner_power__successful(self, stop_service_patch, dict_patch):
        needs = {"cpu": 2, "ram": 3, "gpu": 5, "disk": 7, "network": 11}
        mock.m.contact_microservice.return_value = mock.MagicMock()

        given_per = mock.MagicMock()
        expected_per = mock.MagicMock()
        expected_arguments = [mock.m.contact_microservice(), needs]
        results = [given_per, expected_per]
        dict_patch.side_effect = lambda e: self.assertEqual(expected_arguments.pop(0), e) or results.pop(0)

        expected_result = (expected_per, given_per), {}
        actual_result = essentials.change_miner_power(0.8, "the-miner", "my-device", "user")

        self.assertEqual(expected_result, actual_result)
        stop_service_patch.assert_called_with("my-device", "the-miner", "user")
        mock.m.contact_microservice.assert_called_with(
            "device",
            ["hardware", "register"],
            {
                "user": "user",
                "service_uuid": "the-miner",
                "device_uuid": "my-device",
                "cpu": 2 * 0.8,
                "ram": 3 * 0.8,
                "gpu": 5 * 0.8,
                "disk": 7 * 0.8,
                "network": 11 * 0.8,
            },
        )

    @patch("resources.essentials.get_device_owner")
    def test__controls_device__is_owner(self, get_device_owner_patch):
        get_device_owner_patch.return_value = "user"

        self.assertTrue(essentials.controls_device("the-device", "user"))
        get_device_owner_patch.assert_called_with("the-device")

    @patch("resources.essentials.game_content.part_owner")
    @patch("resources.essentials.get_device_owner")
    def test__controls_device__is_part_owner(self, get_device_owner_patch, part_owner_patch):
        get_device_owner_patch.return_value = "someone-else"
        part_owner_patch.return_value = True

        self.assertTrue(essentials.controls_device("the-device", "user"))
        get_device_owner_patch.assert_called_with("the-device")
        part_owner_patch.assert_called_with("the-device", "user")

    @patch("resources.essentials.game_content.part_owner")
    @patch("resources.essentials.get_device_owner")
    def test__controls_device__access_denied(self, get_device_owner_patch, part_owner_patch):
        get_device_owner_patch.return_value = "someone-else"
        part_owner_patch.return_value = False

        self.assertFalse(essentials.controls_device("the-device", "user"))
        get_device_owner_patch.assert_called_with("the-device")
        part_owner_patch.assert_called_with("the-device", "user")

    def test__check_device_online(self):
        result = mock.MagicMock()
        mock.m.contact_microservice.return_value = {"online": result}
        self.assertEqual(result, essentials.check_device_online("the-device"))
        mock.m.contact_microservice.assert_called_with("device", ["ping"], {"device_uuid": "the-device"})

    def test__get_device_owner(self):
        mock.m.contact_microservice.return_value = {"owner": "some-user"}
        expected_result = "some-user"
        actual_result = essentials.get_device_owner("some-device")

        self.assertEqual(expected_result, actual_result)
        mock.m.contact_microservice.assert_called_with("device", ["owner"], {"device_uuid": "some-device"})

    def test__exists_wallet(self):
        response = mock.MagicMock()
        mock.m.contact_microservice.return_value = {"exists": response}

        actual_result = essentials.exists_wallet("the-wallet")

        self.assertEqual(response, actual_result)
        mock.m.contact_microservice.assert_called_with("currency", ["exists"], {"source_uuid": "the-wallet"})

    def test__get_wallet_owner__does_not_exist(self):
        mock.m.contact_microservice.return_value = {"error": "blubb"}

        actual_result = essentials.get_wallet_owner("the-wallet")

        self.assertEqual(None, actual_result)
        mock.m.contact_microservice.assert_called_with("currency", ["owner"], {"source_uuid": "the-wallet"})

    def test__get_wallet_owner__successful(self):
        mock.m.contact_microservice.return_value = {"owner": "blubb"}

        actual_result = essentials.get_wallet_owner("the-wallet")

        self.assertEqual("blubb", actual_result)
        mock.m.contact_microservice.assert_called_with("currency", ["owner"], {"source_uuid": "the-wallet"})

    def test__update_miner(self):
        mock_miner = mock.MagicMock()
        mock_miner.update_miner.return_value = 1337

        essentials.update_miner(mock_miner)

        mock.m.contact_microservice.assert_called_with(
            "currency", ["put"], {"destination_uuid": mock_miner.wallet, "amount": 1337, "create_transaction": False}
        )

    @patch("resources.essentials.config", {"services": {"ssh": {"auto_start": False}}})
    @patch("resources.essentials.Service.create")
    def test__create_service__default__no_auto_start(self, service_patch):
        mock_service = mock.MagicMock()

        def service_create(uuid, dev, user, name, speed, running):
            self.assertRegex(uuid, r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")
            self.assertEqual("my-device", dev)
            self.assertEqual("user", user)
            self.assertEqual("ssh", name)
            self.assertEqual(0, speed)
            self.assertEqual(False, running)

            return mock_service

        service_patch.side_effect = service_create

        expected_result = mock_service.serialize
        actual_result = essentials.create_service("ssh", {"device_uuid": "my-device"}, "user")

        self.assertEqual(expected_result, actual_result)
        service_patch.assert_called_once()

    @patch("resources.essentials.config", {"services": {"ssh": {"auto_start": True}}})
    @patch("resources.essentials.register_service")
    @patch("resources.essentials.Service.create")
    def test__create_service__default__auto_start_failed(self, service_patch, register_patch):
        mock_service = mock.MagicMock()

        def service_create(uuid, dev, user, name, speed, running):
            register_patch.assert_called_with("my-device", uuid, "ssh", "user")
            self.assertRegex(uuid, r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")
            self.assertEqual("my-device", dev)
            self.assertEqual("user", user)
            self.assertEqual("ssh", name)
            self.assertEqual(0, speed)
            self.assertEqual(False, running)

            return mock_service

        service_patch.side_effect = service_create
        register_patch.return_value = -1

        expected_result = mock_service.serialize
        actual_result = essentials.create_service("ssh", {"device_uuid": "my-device"}, "user")

        self.assertEqual(expected_result, actual_result)
        service_patch.assert_called_once()

    @patch("resources.essentials.config", {"services": {"ssh": {"auto_start": True}}})
    @patch("resources.essentials.register_service")
    @patch("resources.essentials.Service.create")
    def test__create_service__default__with_auto_start(self, service_patch, register_patch):
        mock_service = mock.MagicMock()

        def service_create(uuid, dev, user, name, speed, running):
            register_patch.assert_called_with("my-device", uuid, "ssh", "user")
            self.assertRegex(uuid, r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")
            self.assertEqual("my-device", dev)
            self.assertEqual("user", user)
            self.assertEqual("ssh", name)
            self.assertEqual(register_patch(), speed)
            self.assertEqual(True, running)

            return mock_service

        service_patch.side_effect = service_create

        expected_result = mock_service.serialize
        actual_result = essentials.create_service("ssh", {"device_uuid": "my-device"}, "user")

        self.assertEqual(expected_result, actual_result)
        service_patch.assert_called_once()

    @patch("resources.essentials.config", {"services": {"bruteforce": {"auto_start": False}}})
    @patch("resources.essentials.Bruteforce.create")
    @patch("resources.essentials.Service.create")
    def test__create_service__bruteforce(self, service_patch, bruteforce_patch):
        mock_service = mock.MagicMock()

        def service_create(uuid, dev, user, name, speed, running):
            bruteforce_patch.assert_called_with(uuid)
            self.assertRegex(uuid, r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")
            self.assertEqual("my-device", dev)
            self.assertEqual("user", user)
            self.assertEqual("bruteforce", name)
            self.assertEqual(0, speed)
            self.assertEqual(False, running)

            return mock_service

        service_patch.side_effect = service_create

        expected_result = mock_service.serialize
        actual_result = essentials.create_service("bruteforce", {"device_uuid": "my-device"}, "user")

        self.assertEqual(expected_result, actual_result)
        service_patch.assert_called_once()

    def test__create_service__miner__invalid_request(self):
        self.assertEqual(invalid_request, essentials.create_service("miner", {"device_uuid": "my-device"}, "user"))
        self.assertEqual(
            invalid_request,
            essentials.create_service("miner", {"device_uuid": "my-device", "wallet_uuid": ["not-a-string"]}, "user"),
        )

    @patch("resources.essentials.config", {"services": {"miner": {"auto_start": False}}})
    @patch("resources.essentials.exists_wallet")
    def test__create_service__miner__wallet_not_found(self, wallet_patch):
        wallet_patch.return_value = False

        expected_result = wallet_not_found
        actual_result = essentials.create_service(
            "miner", {"device_uuid": "my-device", "wallet_uuid": "wallet"}, "user"
        )

        self.assertEqual(expected_result, actual_result)
        wallet_patch.assert_called_with("wallet")

    @patch("resources.essentials.config", {"services": {"miner": {"auto_start": False}}})
    @patch("resources.essentials.exists_wallet")
    @patch("resources.essentials.Miner.create")
    @patch("resources.essentials.Service.create")
    def test__create_service__miner__successful(self, service_patch, miner_patch, wallet_patch):
        mock_service = mock.MagicMock()
        wallet_patch.return_value = True

        def service_create(uuid, dev, user, name, speed, running):
            miner_patch.assert_called_with(uuid, "wallet")
            self.assertRegex(uuid, r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")
            self.assertEqual("my-device", dev)
            self.assertEqual("user", user)
            self.assertEqual("miner", name)
            self.assertEqual(0, speed)
            self.assertEqual(False, running)

            return mock_service

        service_patch.side_effect = service_create

        expected_result = mock_service.serialize
        actual_result = essentials.create_service(
            "miner", {"device_uuid": "my-device", "wallet_uuid": "wallet"}, "user"
        )

        self.assertEqual(expected_result, actual_result)
        wallet_patch.assert_called_with("wallet")
        service_patch.assert_called_once()

    @patch("resources.essentials.stop_service")
    def test__delete_one_service__bruteforce(self, stop_patch):
        mock_bruteforce = mock.MagicMock()
        self.query_bruteforce.get.return_value = mock_bruteforce
        mock_service = mock.MagicMock()
        mock_service.name = "bruteforce"

        to_delete = [mock_bruteforce, mock_service]
        mock.wrapper.session.delete.side_effect = to_delete.remove

        essentials.delete_one_service(mock_service)

        self.query_bruteforce.get.assert_called_with(mock_service.uuid)
        self.assertFalse(to_delete)
        stop_patch.assert_called_with(mock_service.device, mock_service.uuid, mock_service.owner)
        mock.wrapper.session.commit.assert_called_with()

    @patch("resources.essentials.update_miner")
    @patch("resources.essentials.stop_service")
    def test__delete_one_service__miner(self, stop_patch, update_patch):
        mock_miner = mock.MagicMock()
        self.query_miner.get.return_value = mock_miner
        mock_service = mock.MagicMock()
        mock_service.name = "miner"

        to_delete = [mock_miner, mock_service]
        mock.wrapper.session.delete.side_effect = to_delete.remove

        essentials.delete_one_service(mock_service)

        self.query_miner.get.assert_called_with(mock_service.uuid)
        update_patch.assert_called_with(mock_miner)
        self.assertFalse(to_delete)
        stop_patch.assert_called_with(mock_service.device, mock_service.uuid, mock_service.owner)
        mock.wrapper.session.commit.assert_called_with()

    @patch(
        "resources.essentials.config",
        {
            "services": {
                "ssh": {
                    "needs": {"cpu": 42, "ram": 1337},
                    "speedm": lambda expected, given: {"expected": expected, "given": given},
                }
            }
        },
    )
    def test__register_service__could_not_start_service(self):
        needs = {"cpu": 42, "ram": 1337}
        mock.m.contact_microservice.return_value = {"error": "some-error"}

        expected_result = -1
        actual_result = essentials.register_service("the-device", "ssh-service", "ssh", "user")

        self.assertEqual(expected_result, actual_result)
        mock.m.contact_microservice.assert_called_with(
            "device",
            ["hardware", "register"],
            {"device_uuid": "the-device", "service_uuid": "ssh-service", "user": "user", **needs},
        )

    @patch(
        "resources.essentials.config",
        {
            "services": {
                "ssh": {
                    "needs": {"cpu": 42, "ram": 1337},
                    "speedm": lambda expected, given: {"expected": expected, "given": given},
                }
            }
        },
    )
    @patch("resources.essentials.game_content.dict2tuple")
    def test__register_service__successful(self, dict_patch):
        needs = {"cpu": 42, "ram": 1337}
        mock.m.contact_microservice.return_value = mock.MagicMock()

        expected_params = [mock.m.contact_microservice(), needs]
        results = ["given_per", "expected_per"]
        dict_patch.side_effect = lambda arg: self.assertEqual(expected_params.pop(0), arg) or results.pop(0)

        expected_result = {"expected": "expected_per", "given": "given_per"}
        actual_result = essentials.register_service("the-device", "ssh-service", "ssh", "user")

        self.assertEqual(expected_result, actual_result)
        mock.m.contact_microservice.assert_called_with(
            "device",
            ["hardware", "register"],
            {"device_uuid": "the-device", "service_uuid": "ssh-service", "user": "user", **needs},
        )

    def test__stop_service(self):
        essentials.stop_service("my-device", "telnet-service", "some-user")

        mock.m.contact_microservice.assert_called_with(
            "device",
            ["hardware", "stop"],
            {"device_uuid": "my-device", "service_uuid": "telnet-service", "user": "some-user"},
        )

    @patch("resources.essentials.update_miner")
    def test__stop_services(self, update_patch):
        def create_service(name):
            s = mock.MagicMock()
            s.name = name
            return s

        services = [create_service("ssh"), create_service("bruteforce"), create_service("miner")]
        self.query_miner.get.return_value = miner = mock.MagicMock()
        self.query_bruteforce.get.return_value = bruteforce = mock.MagicMock()
        self.query_service.filter_by.return_value = services

        essentials.stop_services("the-device")

        self.query_service.filter_by.assert_called_with(device="the-device")

        self.query_bruteforce.get.assert_called_with(services[1].uuid)
        self.assertEqual(None, bruteforce.target_device)
        self.assertEqual(None, bruteforce.target_service)
        self.assertEqual(None, bruteforce.started)

        self.query_miner.get.assert_called_with(services[2].uuid)
        update_patch.assert_called_with(miner)
        self.assertEqual(None, miner.started)

        for service in services:
            self.assertEqual(False, service.running)

        mock.wrapper.session.commit.assert_called_with()

    @patch("resources.essentials.delete_one_service")
    def test__delete_services(self, delete_patch):
        services = [mock.MagicMock() for _ in range(5)]
        self.query_service.filter_by.return_value = services.copy()
        delete_patch.side_effect = services.remove

        essentials.delete_services("my-device")

        self.query_service.filter_by.assert_called_with(device="my-device")
        self.assertFalse(services)
