from importlib import machinery, util
from unittest import TestCase

from mock.mock_loader import mock
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

    def test__run_as_main(self):
        import_app("__main__")

        mock.wrapper.Base.metadata.create_all.assert_called_with(bind=mock.wrapper.engine)
        mock.m.run.assert_called_with()

    def test__import_as_module(self):
        import_app()

        mock.wrapper.Base.metadata.create_all.assert_not_called()
        mock.m.run.assert_not_called()

    def test__endpoints_available(self):
        app = import_app("__main__")
        elements = [getattr(app, element_name) for element_name in dir(app)]

        registered_user_endpoints = mock.user_endpoints.copy()
        registered_ms_endpoints = mock.ms_endpoints.copy()

        expected_user_endpoints = [
            (["public_info"], standard_scheme),
            (["use"], None),
            (["private_info"], standard_scheme),
            (["toggle"], standard_scheme),
            (["delete"], standard_scheme),
            (["list"], device_scheme),
            (["create"], None),
            (["part_owner"], device_scheme),
            (["bruteforce", "attack"], attack_scheme),
            (["bruteforce", "status"], standard_scheme),
            (["bruteforce", "stop"], standard_scheme),
            (["miner", "get"], service_scheme),
            (["miner", "list"], wallet_scheme),
            (["miner", "wallet"], miner_set_wallet_scheme),
            (["miner", "power"], miner_set_power_scheme),
        ]

        expected_ms_endpoints = [
            ["check_part_owner"],
            ["hardware", "scale"],
            ["hardware", "stop"],
            ["hardware", "delete"],
            ["miner", "collect"],
        ]

        for path, requires in expected_user_endpoints:
            self.assertIn((path, requires), registered_user_endpoints)
            registered_user_endpoints.remove((path, requires))
            self.assertIn(mock.user_endpoint_handlers[tuple(path)], elements)

        for path in expected_ms_endpoints:
            self.assertIn(path, registered_ms_endpoints)
            registered_ms_endpoints.remove(path)
            self.assertIn(mock.ms_endpoint_handlers[tuple(path)], elements)

        self.assertFalse(registered_user_endpoints)
        self.assertFalse(registered_ms_endpoints)
