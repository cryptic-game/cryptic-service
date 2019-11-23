from importlib import machinery, util
from unittest import TestCase

from mock.mock_loader import mock
from resources import service, bruteforce, miner
from resources.errors import service_exists, device_online, has_service_and_device, device_accessible
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

        service_errors = (service_exists(), device_online, device_accessible)
        bruteforce_errors = (service_exists("bruteforce"), device_online, device_accessible)
        miner_errors = (
            service_exists("miner", device_required=False),
            device_online,
            device_accessible,
        )
        expected_user_endpoints = [
            (["public_info"], standard_scheme, service.public_info, service_exists(), device_online),
            (["use"], None, service.use, has_service_and_device, *service_errors),
            (["private_info"], standard_scheme, service.private_info, *service_errors),
            (["toggle"], standard_scheme, service.toggle, *service_errors),
            (["delete"], standard_scheme, service.delete_service, *service_errors),
            (["list"], device_scheme, service.list_services, device_online, device_accessible),
            (["create"], None, service.create, device_online, device_accessible),
            (["part_owner"], device_scheme, service.part_owner, device_online),
            (["list_part_owner"], {}, service.list_part_owner),
            (["bruteforce", "attack"], attack_scheme, bruteforce.attack, *bruteforce_errors),
            (["bruteforce", "status"], standard_scheme, bruteforce.status, *bruteforce_errors),
            (["bruteforce", "stop"], standard_scheme, bruteforce.stop, *bruteforce_errors),
            (["miner", "get"], service_scheme, miner.get, *miner_errors),
            (["miner", "list"], wallet_scheme, miner.list_miners),
            (["miner", "wallet"], miner_set_wallet_scheme, miner.set_wallet, *miner_errors),
            (["miner", "power"], miner_set_power_scheme, miner.set_power, *miner_errors),
        ]

        expected_ms_endpoints = [
            (["device_init"], service.device_init),
            (["device_restart"], service.device_restart),
            (["check_part_owner"], service.check_part_owner),
            (["hardware", "scale"], service.hardware_scale),
            (["hardware", "stop"], service.hardware_stop),
            (["hardware", "delete"], service.hardware_delete),
            (["miner", "stop"], miner.miner_stop),
            (["miner", "collect"], miner.collect),
            (["delete_user"], service.delete_user),
        ]

        for path, requires, func, *errors in expected_user_endpoints:
            self.assertIn((path, requires), registered_user_endpoints)
            endpoint_handler = mock.user_endpoint_handlers[tuple(path)]
            registered_user_endpoints.remove((path, requires))
            self.assertIn(endpoint_handler, elements)
            self.assertEqual(func, endpoint_handler)
            if errors:
                self.assertEqual(len(errors), len(endpoint_handler.__errors__))
                for a, b in zip(errors, endpoint_handler.__errors__):
                    if a == b:
                        continue
                    self.assertEqual(a.__qualname__, b.__qualname__)
                    self.assertEqual(a.__closure__, b.__closure__)
            else:
                self.assertNotIn("__errors__", dir(endpoint_handler))

        for path, func, *errors in expected_ms_endpoints:
            self.assertIn(path, registered_ms_endpoints)
            endpoint_handler = mock.ms_endpoint_handlers[tuple(path)]
            registered_ms_endpoints.remove(path)
            self.assertIn(endpoint_handler, elements)
            self.assertEqual(func, endpoint_handler)
            if errors:
                self.assertEqual(len(errors), len(endpoint_handler.__errors__))
                for a, b in zip(errors, endpoint_handler.__errors__):
                    if a == b:
                        continue
                    self.assertEqual(a.__qualname__, b.__qualname__)
                    self.assertEqual(a.__closure__, b.__closure__)
            else:
                self.assertNotIn("__errors__", dir(endpoint_handler))
        self.assertFalse(registered_user_endpoints)
        self.assertFalse(registered_ms_endpoints)
