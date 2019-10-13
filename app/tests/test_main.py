from importlib import machinery, util
from unittest import TestCase

from mock.mock_loader import mock
from resources import service, bruteforce, miner
from schemes import (
    standard_scheme,
    device_scheme,
    attack_scheme,
    service_scheme,
    wallet_scheme,
    miner_set_wallet_scheme,
    miner_set_power_scheme,
)


def import_app(name: str = "app"):
    return machinery.SourceFileLoader(name, util.find_spec("app").origin).load_module()


def import_main(name: str = "main"):
    return machinery.SourceFileLoader(name, util.find_spec("main").origin).load_module()


class TestApp(TestCase):
    def setUp(self):
        mock.reset_mocks()

    def test__microservice_setup(self):
        app = import_app()

        mock.get_config.assert_called_with()
        self.assertEqual(mock.get_config(), app.config)

        mock.MicroService.assert_called_with("service")
        self.assertEqual(mock.MicroService(), app.m)

        mock.m.get_wrapper.assert_called_with()
        self.assertEqual(mock.m.get_wrapper(), app.wrapper)

    def test__microservice_setup_called(self):
        main = import_main()
        self.assertEqual(import_app(), main.app)

    def test__run_as_main(self):
        import_main("__main__")

        mock.wrapper.Base.metadata.create_all.assert_called_with(bind=mock.wrapper.engine)
        mock.m.run.assert_called_with()

    def test__import_as_module(self):
        import_main()

        mock.wrapper.Base.metadata.create_all.assert_not_called()
        mock.m.run.assert_not_called()

    def test__endpoints_available(self):
        main = import_main("__main__")
        elements = [getattr(main, element_name) for element_name in dir(main)]

        registered_user_endpoints = mock.user_endpoints.copy()
        registered_ms_endpoints = mock.ms_endpoints.copy()

        expected_user_endpoints = [
            (["public_info"], standard_scheme, service.public_info),
            (["use"], None, service.use),
            (["private_info"], standard_scheme, service.private_info),
            (["toggle"], standard_scheme, service.toggle),
            (["delete"], standard_scheme, service.delete_service),
            (["list"], device_scheme, service.list_services),
            (["create"], None, service.create),
            (["part_owner"], device_scheme, service.part_owner),
            (["list_part_owner"], {}, service.list_part_owner),
            (["bruteforce", "attack"], attack_scheme, bruteforce.attack),
            (["bruteforce", "status"], standard_scheme, bruteforce.status),
            (["bruteforce", "stop"], standard_scheme, bruteforce.stop),
            (["miner", "get"], service_scheme, miner.get),
            (["miner", "list"], wallet_scheme, miner.list_miners),
            (["miner", "wallet"], miner_set_wallet_scheme, miner.set_wallet),
            (["miner", "power"], miner_set_power_scheme, miner.set_power),
        ]

        expected_ms_endpoints = [
            (["check_part_owner"], service.check_part_owner),
            (["hardware", "scale"], service.hardware_scale),
            (["hardware", "stop"], service.hardware_stop),
            (["hardware", "delete"], service.hardware_delete),
            (["miner", "stop"], miner.miner_stop),
            (["miner", "collect"], miner.collect),
            (["delete_user"], service.delete_user),
        ]

        for path, requires, func in expected_user_endpoints:
            self.assertIn((path, requires), registered_user_endpoints)
            registered_user_endpoints.remove((path, requires))
            self.assertIn(mock.user_endpoint_handlers[tuple(path)], elements)
            self.assertEqual(func, mock.user_endpoint_handlers[tuple(path)])

        for path, func in expected_ms_endpoints:
            self.assertIn(path, registered_ms_endpoints)
            registered_ms_endpoints.remove(path)
            self.assertIn(mock.ms_endpoint_handlers[tuple(path)], elements)
            self.assertEqual(func, mock.ms_endpoint_handlers[tuple(path)])

        self.assertFalse(registered_user_endpoints)
        self.assertFalse(registered_ms_endpoints)
