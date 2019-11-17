from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.service import Service
from resources import errors
from resources.errors import MicroserviceException
from schemes import invalid_request, service_not_found, device_not_found, device_not_online, permission_denied


class TestErrors(TestCase):
    def setUp(self):
        mock.reset_mocks()

        self.query_service = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {Service: self.query_service}.__getitem__

    def test__has_service_and_device__missing(self):
        with self.assertRaises(MicroserviceException) as context:
            errors.has_service_and_device({}, "")
        self.assertEqual(invalid_request, context.exception.error)

        with self.assertRaises(MicroserviceException) as context:
            errors.has_service_and_device({"service_uuid": ""}, "")
        self.assertEqual(invalid_request, context.exception.error)

        with self.assertRaises(MicroserviceException) as context:
            errors.has_service_and_device({"device_uuid": ""}, "")
        self.assertEqual(invalid_request, context.exception.error)

    def test__has_service_and_device__no_string(self):
        with self.assertRaises(MicroserviceException) as context:
            errors.has_service_and_device({"service_uuid": None, "device_uuid": 7}, "")
        self.assertEqual(invalid_request, context.exception.error)

        with self.assertRaises(MicroserviceException) as context:
            errors.has_service_and_device({"service_uuid": "", "device_uuid": 42}, "")
        self.assertEqual(invalid_request, context.exception.error)

        with self.assertRaises(MicroserviceException) as context:
            errors.has_service_and_device({"service_uuid": 1337, "device_uuid": ""}, "")
        self.assertEqual(invalid_request, context.exception.error)

    def test__has_service_and_device__successful(self):
        self.assertEqual((), errors.has_service_and_device({"service_uuid": "", "device_uuid": ""}, ""))

    def test__service_exists__device_required__service_not_found(self):
        self.query_service.filter_by().first.return_value = None

        with self.assertRaises(MicroserviceException) as context:
            errors.service_exists(None, True)({"service_uuid": "s", "device_uuid": "d"}, "")

        self.assertEqual(service_not_found, context.exception.error)
        self.query_service.filter_by.assert_called_with(uuid="s", device="d")

    def test__service_exists__device_not_required__service_not_found(self):
        self.query_service.filter_by().first.return_value = None

        with self.assertRaises(MicroserviceException) as context:
            errors.service_exists(None, False)({"service_uuid": "s"}, "")

        self.assertEqual(service_not_found, context.exception.error)
        self.query_service.filter_by.assert_called_with(uuid="s")

    def test__service_exists__device_not_required__name_required__service_not_found(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.name = "not-the-name"

        with self.assertRaises(MicroserviceException) as context:
            errors.service_exists("name", False)({"service_uuid": "s"}, "")

        self.assertEqual(service_not_found, context.exception.error)
        self.query_service.filter_by.assert_called_with(uuid="s")

    def test__service_exists__device_not_required__name_required__successful(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()
        mock_service.name = "name"

        self.assertEqual(mock_service, errors.service_exists("name", False)({"service_uuid": "s"}, ""))
        self.query_service.filter_by.assert_called_with(uuid="s")

    def test__service_exists__device_not_required__name_not_required__successful(self):
        mock_service = self.query_service.filter_by().first.return_value = mock.MagicMock()

        self.assertEqual(mock_service, errors.service_exists(None, False)({"service_uuid": "s"}, ""))
        self.query_service.filter_by.assert_called_with(uuid="s")

    @patch("resources.errors.exists_device")
    def test__device_online__device_not_found(self, exists_device_patch):
        exists_device_patch.return_value = False

        with self.assertRaises(MicroserviceException) as context:
            errors.device_online({"device_uuid": "the-device"}, "", None)

        self.assertEqual(device_not_found, context.exception.error)
        exists_device_patch.assert_called_with("the-device")

    @patch("resources.errors.check_device_online")
    @patch("resources.errors.exists_device")
    def test__device_online__device_not_online(self, exists_device_patch, check_online_patch):
        exists_device_patch.return_value = True
        check_online_patch.return_value = False

        with self.assertRaises(MicroserviceException) as context:
            errors.device_online({"device_uuid": "the-device"}, "", None)

        self.assertEqual(device_not_online, context.exception.error)
        exists_device_patch.assert_called_with("the-device")
        check_online_patch.assert_called_with("the-device")

    @patch("resources.errors.check_device_online")
    @patch("resources.errors.exists_device")
    def test__device_online__successful(self, exists_device_patch, check_online_patch):
        exists_device_patch.return_value = True
        check_online_patch.return_value = True

        self.assertEqual((), errors.device_online({"device_uuid": "the-device"}, "", None))
        exists_device_patch.assert_called_with("the-device")
        check_online_patch.assert_called_with("the-device")

    @patch("resources.errors.check_device_online")
    @patch("resources.errors.exists_device")
    def test__device_online__successful_with_service(self, exists_device_patch, check_online_patch):
        mock_service = mock.MagicMock()
        exists_device_patch.return_value = True
        check_online_patch.return_value = True

        self.assertEqual(mock_service, errors.device_online({}, "", mock_service))
        exists_device_patch.assert_called_with(mock_service.device)
        check_online_patch.assert_called_with(mock_service.device)

    @patch("resources.errors.controls_device")
    def test__device_accessible__permission_denied(self, controls_device_patch):
        controls_device_patch.return_value = False

        with self.assertRaises(MicroserviceException) as context:
            errors.device_accessible({"device_uuid": "the-device"}, "the-user", None)

        self.assertEqual(permission_denied, context.exception.error)
        controls_device_patch.assert_called_with("the-device", "the-user")

    @patch("resources.errors.controls_device")
    def test__device_accessible__successful(self, controls_device_patch):
        controls_device_patch.return_value = True

        self.assertEqual((), errors.device_accessible({"device_uuid": "the-device"}, "the-user", None))
        controls_device_patch.assert_called_with("the-device", "the-user")

    @patch("resources.errors.controls_device")
    def test__device_accessible__successful_with_service(self, controls_device_patch):
        mock_service = mock.MagicMock()
        controls_device_patch.return_value = True

        self.assertEqual(mock_service, errors.device_accessible({}, "the-user", mock_service))
        controls_device_patch.assert_called_with(mock_service.device, "the-user")
