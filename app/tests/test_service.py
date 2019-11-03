from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.bruteforce import Bruteforce
from models.miner import Miner
from models.service import Service
from resources import service, game_content
from schemes import (
    unknown_service,
    invalid_request,
    service_cannot_be_used,
    permission_denied,
    service_not_found,
    cannot_toggle_directly,
    success_scheme,
    device_not_found,
    service_not_supported,
    already_own_this_service,
    could_not_start_service,
    cannot_delete_enforced_service,
)


class TestService(TestCase):
    def setUp(self):
        mock.reset_mocks()

        self.query_service = mock.MagicMock()
        service.func = self.sqlalchemy_func = mock.MagicMock()
        self.query_func_count = mock.MagicMock()
        self.query_bruteforce = mock.MagicMock()
        self.query_miner = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {
            Service: self.query_service,
            Bruteforce: self.query_bruteforce,
            Miner: self.query_miner,
            self.sqlalchemy_func.count(): self.query_func_count,
        }.__getitem__

    def test__switch(self):
        self.assertEqual(game_content.portscan, service.switch["portscan"])

    def test__user_endpoint__public_info__service_not_found(self):
        self.query_service.filter_by().first.return_value = None
        self.assertEqual(unknown_service, service.public_info({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    def test__user_endpoint__public_info__service_not_running(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.running_port = None
        mock_service.running = False
        self.assertEqual(unknown_service, service.public_info({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    def test__user_endpoint__public_info__successful(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.running_port = 42
        mock_service.running = True

        expected_result = mock_service.public_data()
        actual_result = service.public_info({"service_uuid": "s", "device_uuid": "d"}, "u")

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")
        mock_service.public_data.assert_called_with()

    def test__user_endpoint__use__invalid_request(self):
        self.assertEqual(invalid_request, service.use({}, ""))
        self.assertEqual(invalid_request, service.use({"device_uuid": "uuid"}, ""))
        self.assertEqual(invalid_request, service.use({"service_uuid": "uuid"}, ""))

        self.assertEqual(invalid_request, service.use({"device_uuid": None, "service_uuid": "uuid"}, ""))
        self.assertEqual(invalid_request, service.use({"device_uuid": "uuid", "service_uuid": None}, ""))

    def test__user_endpoint__use__service_not_found(self):
        self.query_service.filter_by().first.return_value = None
        self.assertEqual(unknown_service, service.use({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    @patch("resources.service.game_content.part_owner")
    def test__user_endpoint__use__permission_denied(self, part_owner_patch):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.owner = "someone-else"
        part_owner_patch.return_value = False
        self.assertEqual(unknown_service, service.use({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")
        part_owner_patch.assert_called_with("d", "u")

    def test__user_endpoint__use__service_cannot_be_used(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.owner = "u"
        mock_service.name = "not-in-dict"
        self.assertEqual(service_cannot_be_used, service.use({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    @patch("resources.service.switch", {"tool": lambda data, user: {"from": "tool", "data": data, "user": user}})
    def test__user_endpoint__use__successful(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.owner = "u"
        mock_service.name = "tool"

        data = {"service_uuid": "s", "device_uuid": "d"}
        expected_result = {"from": "tool", "data": data, "user": "u"}
        actual_result = service.use(data, "u")

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    def test__user_endpoint__private_info__unknown_service(self):
        self.query_service.filter_by().first.return_value = None
        self.assertEqual(unknown_service, service.private_info({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    def test__user_endpoint__private_info__permission_denied(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.check_access.return_value = False
        self.assertEqual(permission_denied, service.private_info({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")
        mock_service.check_access.assert_called_with("u")

    def test__user_endpoint__private_info__successful(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.check_access.return_value = True

        expected_result = mock_service.serialize
        actual_result = service.private_info({"service_uuid": "s", "device_uuid": "d"}, "u")

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")
        mock_service.check_access.assert_called_with("u")

    def test__user_endpoint__toggle__service_not_found(self):
        self.query_service.filter_by().first.return_value = None
        self.assertEqual(service_not_found, service.toggle({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    def test__user_endpoint__toggle__permission_denied(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.owner = "someone-else"
        self.assertEqual(permission_denied, service.toggle({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    @patch("resources.service.config", {"services": {"miner": {"toggleable": False}}})
    def test__user_endpoint__toggle__cannot_toggle_directly(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.owner = "u"
        mock_service.name = "miner"

        expected_result = cannot_toggle_directly
        actual_result = service.toggle({"service_uuid": "s", "device_uuid": "d"}, "u")

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    @patch("resources.service.config", {"services": {"ssh": {"toggleable": True}}})
    @patch("resources.service.register_service")
    def test__user_endpoint__toggle__could_not_start_service(self, register_patch):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.owner = "u"
        mock_service.name = "ssh"
        mock_service.running = False
        register_patch.return_value = -1

        expected_result = could_not_start_service
        actual_result = service.toggle({"service_uuid": "s", "device_uuid": "d"}, "u")

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")
        register_patch.assert_called_with(mock_service.device, mock_service.uuid, "ssh", "u")
        self.assertEqual(False, mock_service.running)

    @patch("resources.service.config", {"services": {"ssh": {"toggleable": True}}})
    @patch("resources.service.register_service")
    def test__user_endpoint__toggle__starting(self, register_patch):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.owner = "u"
        mock_service.name = "ssh"
        mock_service.running = False

        expected_result = mock_service.serialize
        actual_result = service.toggle({"service_uuid": "s", "device_uuid": "d"}, "u")

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")
        register_patch.assert_called_with(mock_service.device, mock_service.uuid, "ssh", "u")
        self.assertEqual(True, mock_service.running)
        mock.wrapper.session.commit.assert_called_with()

    @patch("resources.service.config", {"services": {"ssh": {"toggleable": True}}})
    @patch("resources.service.stop_service")
    def test__user_endpoint__toggle__stopping(self, stop_patch):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.owner = "u"
        mock_service.name = "ssh"
        mock_service.running = True

        expected_result = mock_service.serialize
        actual_result = service.toggle({"service_uuid": "s", "device_uuid": "d"}, "u")

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")
        stop_patch.assert_called_with(mock_service.device, mock_service.uuid, "u")
        self.assertEqual(False, mock_service.running)
        mock.wrapper.session.commit.assert_called_with()

    def test__user_endpoint__delete__service_not_found(self):
        self.query_service.filter_by().first.return_value = None
        self.assertEqual(service_not_found, service.delete_service({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    def test__user_endpoint__delete__cannot_delete_ssh(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.name = "ssh"
        self.assertEqual(
            cannot_delete_enforced_service, service.delete_service({"service_uuid": "s", "device_uuid": "d"}, "u")
        )
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    @patch("resources.service.controls_device")
    def test__user_endpoint__delete__permission_denied(self, controls_device_patch):
        self.query_service.filter_by().first.return_value = mock.MagicMock()
        controls_device_patch.return_value = False
        self.assertEqual(permission_denied, service.delete_service({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")
        controls_device_patch.assert_called_with("d", "u")

    @patch("resources.service.delete_one_service")
    @patch("resources.service.controls_device")
    def test__user_endpoint__delete__successful(self, controls_device_patch, delete_patch):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        controls_device_patch.return_value = True
        self.assertEqual(success_scheme, service.delete_service({"service_uuid": "s", "device_uuid": "d"}, "u"))
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")
        controls_device_patch.assert_called_with("d", "u")
        delete_patch.assert_called_with(mock_service)

    @patch("resources.service.exists_device")
    def test__user_endpoint__list__device_not_found(self, exists_device_patch):
        exists_device_patch.return_value = False

        expected_result = device_not_found
        actual_result = service.list_services({"device_uuid": "my-device"}, "user")

        self.assertEqual(expected_result, actual_result)
        exists_device_patch.assert_called_with("my-device")

    @patch("resources.service.controls_device")
    @patch("resources.service.exists_device")
    def test__user_endpoint__list__permission_denied(self, exists_device_patch, controls_device_patch):
        exists_device_patch.return_value = True
        controls_device_patch.return_value = False

        expected_result = permission_denied
        actual_result = service.list_services({"device_uuid": "my-device"}, "user")

        self.assertEqual(expected_result, actual_result)
        exists_device_patch.assert_called_with("my-device")
        controls_device_patch.assert_called_with("my-device", "user")

    @patch("resources.service.controls_device")
    @patch("resources.service.exists_device")
    def test__user_endpoint__list__successful(self, exists_device_patch, controls_device_patch):
        exists_device_patch.return_value = True
        controls_device_patch.return_value = True
        services = self.query_service.filter_by().all.return_value = [mock.MagicMock() for _ in range(5)]

        expected_result = {"services": [s.serialize for s in services]}
        actual_result = service.list_services({"device_uuid": "my-device"}, "user")

        self.assertEqual(expected_result, actual_result)
        exists_device_patch.assert_called_with("my-device")
        controls_device_patch.assert_called_with("my-device", "user")
        self.query_service.filter_by.assert_called_with(device="my-device")

    def test__user_endpoint__create__invalid_request(self):
        self.assertEqual(invalid_request, service.create({}, ""))
        self.assertEqual(invalid_request, service.create({"device_uuid": "d"}, ""))
        self.assertEqual(invalid_request, service.create({"name": "n"}, ""))

        self.assertEqual(invalid_request, service.create({"device_uuid": None, "name": "n"}, ""))
        self.assertEqual(invalid_request, service.create({"device_uuid": "d", "name": None}, ""))

    @patch("resources.service.config", {"services": {}})
    def test__user_endpoint__create__service_not_supported(self):
        self.assertEqual(service_not_supported, service.create({"device_uuid": "d", "name": "invalid-service"}, ""))

    @patch("resources.service.config", {"services": {"the-service": {}}})
    @patch("resources.service.exists_device")
    def test__user_endpoint__create__device_not_found(self, exists_device_patch):
        exists_device_patch.return_value = False

        expected_result = device_not_found
        actual_result = service.create({"device_uuid": "my-device", "name": "the-service"}, "user")

        self.assertEqual(expected_result, actual_result)
        exists_device_patch.assert_called_with("my-device")

    @patch("resources.service.config", {"services": {"the-service": {}}})
    @patch("resources.service.controls_device")
    @patch("resources.service.exists_device")
    def test__user_endpoint__create__permission_denied(self, exists_device_patch, controls_device_patch):
        exists_device_patch.return_value = True
        controls_device_patch.return_value = False

        expected_result = permission_denied
        actual_result = service.create({"device_uuid": "my-device", "name": "the-service"}, "user")

        self.assertEqual(expected_result, actual_result)
        exists_device_patch.assert_called_with("my-device")
        controls_device_patch.assert_called_with("my-device", "user")

    @patch("resources.service.config", {"services": {"the-service": {}}})
    @patch("resources.service.get_device_owner")
    @patch("resources.service.controls_device")
    @patch("resources.service.exists_device")
    def test__user_endpoint__create__already_own_this_service(
        self, exists_device_patch, controls_device_patch, get_device_owner_patch
    ):
        exists_device_patch.return_value = True
        controls_device_patch.return_value = True
        self.query_func_count.filter_by().scalar.return_value = 1
        get_device_owner_patch.return_value = "dev-owner"

        expected_result = already_own_this_service
        actual_result = service.create({"device_uuid": "my-device", "name": "the-service"}, "user")

        self.assertEqual(expected_result, actual_result)
        exists_device_patch.assert_called_with("my-device")
        controls_device_patch.assert_called_with("my-device", "user")
        self.sqlalchemy_func.count.assert_called_with(Service.name)
        get_device_owner_patch.assert_called_with("my-device")
        self.query_func_count.filter_by.assert_called_with(owner="dev-owner", device="my-device", name="the-service")

    @patch("resources.service.config", {"services": {"the-service": {}}})
    @patch("resources.service.create_service")
    @patch("resources.service.get_device_owner")
    @patch("resources.service.controls_device")
    @patch("resources.service.exists_device")
    def test__user_endpoint__create__successful(
        self, exists_device_patch, controls_device_patch, get_device_owner_patch, create_patch
    ):
        exists_device_patch.return_value = True
        controls_device_patch.return_value = True
        self.query_func_count.filter_by().scalar.return_value = 0
        get_device_owner_patch.return_value = "dev-owner"

        data = {"device_uuid": "my-device", "name": "the-service"}
        expected_result = create_patch()
        actual_result = service.create(data, "user")

        self.assertEqual(expected_result, actual_result)
        exists_device_patch.assert_called_with("my-device")
        controls_device_patch.assert_called_with("my-device", "user")
        self.sqlalchemy_func.count.assert_called_with(Service.name)
        get_device_owner_patch.assert_called_with("my-device")
        self.query_func_count.filter_by.assert_called_with(owner="dev-owner", device="my-device", name="the-service")
        create_patch.assert_called_with("the-service", data, "dev-owner")

    @patch("resources.service.game_content.part_owner")
    def test__user_endpoint__part_owner(self, part_owner_patch):
        expected_result = {"ok": part_owner_patch()}
        actual_result = service.part_owner({"device_uuid": "some-device"}, "user")

        self.assertEqual(expected_result, actual_result)
        part_owner_patch.assert_called_with("some-device", "user")

    def test__user_endpoint__list_part_owner(self):
        services = self.query_service.filter_by.return_value = [mock.MagicMock() for _ in range(5)]

        expected_result = {"services": [e.serialize for e in services]}
        actual_result = service.list_part_owner({}, "user")

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(part_owner="user")

    @patch("resources.service.create_service")
    def test__ms_endpoint__device_init(self, create_service_patch):
        data = {"device_uuid": "some-device", "user": "foobar"}
        self.assertEqual(success_scheme, service.device_init(data, ""))
        create_service_patch.assert_called_with("ssh", data, "foobar")

    @patch("resources.service.game_content.part_owner")
    def test__ms_endpoint__check_part_owner(self, part_owner_patch):
        expected_result = {"ok": part_owner_patch()}
        actual_result = service.check_part_owner({"device_uuid": "some-device", "user_uuid": "user"}, "")

        self.assertEqual(expected_result, actual_result)
        part_owner_patch.assert_called_with("some-device", "user")

    @patch(
        "resources.service.config",
        {
            "services": {
                "bruteforce": {
                    "needs": {"foo": "bar"},
                    "speedm": lambda e, g: {"from": "speedm", "expected": e, "given": g},
                }
            }
        },
    )
    @patch("resources.service.game_content.dict2tuple")
    def test__ms_endpoint__hardware_scale(self, dict_patch):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.name = "bruteforce"
        old_speed = mock_service.speed
        data = {"service_uuid": mock_service.uuid}
        needs = {"foo": "bar"}
        given_per = mock.MagicMock()
        expected_per = mock.MagicMock()
        expected_params = [data, needs]
        results = [given_per, expected_per]
        dict_patch.side_effect = lambda x: self.assertEqual(expected_params.pop(0), x) or results.pop(0)
        bruteforce = self.query_bruteforce.get.return_value = mock.MagicMock()

        expected_result = success_scheme
        actual_result = service.hardware_scale(data, "user")

        self.assertEqual(expected_result, actual_result)
        self.query_service.filter_by.assert_called_with(uuid=mock_service.uuid)
        self.query_bruteforce.get.assert_called_with(mock_service.uuid)
        bruteforce.update_progress.assert_called_with(old_speed)
        self.assertEqual({"from": "speedm", "expected": expected_per, "given": given_per}, mock_service.speed)
        mock.wrapper.session.commit.assert_called_with()

    @patch("resources.service.stop_services")
    def test__ms_endpoint__hardware_stop(self, stop_patch):
        self.assertEqual(success_scheme, service.hardware_stop({"device_uuid": "the-device"}, ""))
        stop_patch.assert_called_with("the-device")

    @patch("resources.service.delete_services")
    def test__ms_endpoint__hardware_delete(self, delete_patch):
        self.assertEqual(success_scheme, service.hardware_delete({"device_uuid": "the-device"}, ""))
        delete_patch.assert_called_with("the-device")

    def test__ms_endpoint__delete_user(self):
        normal_service = mock.MagicMock()
        bruteforce_service = mock.MagicMock()
        bruteforce_info = mock.MagicMock()
        miner_service = mock.MagicMock()
        miner_info = mock.MagicMock()
        self.query_service.filter_by.return_value = [normal_service, bruteforce_service, miner_service]
        to_delete = [normal_service, bruteforce_service, bruteforce_info, miner_service, miner_info]

        def handle_query_bruteforce(uuid):
            out = mock.MagicMock()
            out.first.return_value = bruteforce_info if uuid == bruteforce_service.uuid else None
            return out

        self.query_bruteforce.filter_by.side_effect = handle_query_bruteforce

        def handle_query_miner(uuid):
            out = mock.MagicMock()
            out.first.return_value = miner_info if uuid == miner_service.uuid else None
            return out

        self.query_miner.filter_by.side_effect = handle_query_miner

        mock.wrapper.session.delete.side_effect = to_delete.remove

        self.assertEqual(success_scheme, service.delete_user({"user_uuid": "user"}, "server"))
        self.query_service.filter_by.assert_called_with(owner="user")
        mock.wrapper.session.commit.assert_called_with()
        self.assertFalse(to_delete)
