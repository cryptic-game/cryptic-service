from scheme import UUID, Float, Integer, Union

invalid_request: dict = {"error": "invalid_request"}

success_scheme: dict = {"ok": True}

already_own_this_service: dict = {"error": "already_own_this_service"}

service_not_supported: dict = {"error": "service_not_supported"}

service_not_running: dict = {"error": "service_not_running"}

permission_denied: dict = {"error": "permission_denied"}

cannot_toggle_directly: dict = {"error": "cannot_toggle_directly"}

device_not_found: dict = {"error": "device_not_found"}

wallet_not_found: dict = {"error": "wallet_not_found"}

miner_not_found: dict = {"error": "miner_not_found"}

service_not_found: dict = {"error": "service_not_found"}

unknown_service: dict = {"error": "unknown_service"}

service_cannot_be_used: dict = {"error": "service_cannot_be_used"}

attack_not_running: dict = {"error": "attack_not_running"}

attack_already_running: dict = {"error": "attack_already_running"}

could_not_start_service: dict = {"error": "could_not_start_service"}

cannot_delete_enforced_service: dict = {"error": "cannot_delete_enforced_service"}

attack_scheme: dict = {"device_uuid": UUID(), "service_uuid": UUID(), "target_service": UUID(), "target_device": UUID()}

standard_scheme: dict = {"device_uuid": UUID(), "service_uuid": UUID()}

device_scheme = {"device_uuid": UUID()}

service_scheme = {"service_uuid": UUID()}

wallet_scheme = {"wallet_uuid": UUID()}

miner_set_wallet_scheme = {"service_uuid": UUID(), "wallet_uuid": UUID()}

miner_set_power_scheme = {
    "service_uuid": UUID(),
    "power": Union([Float(minimum=0.0, maximum=1.0), Integer(minimum=0, maximum=1)]),
}
