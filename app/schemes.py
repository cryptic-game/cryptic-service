from scheme import UUID

invalid_request: dict = {"error": "invalid_request"}

success_scheme: dict = {"ok": True}

multiple_services: dict = {"error": "you_already_own_a_service_with_this_name"}

service_is_not_supported: dict = {"error": "this_service_is_not_supported"}

service_is_not_running: dict = {"error": "this_service_is_not_running"}

permission_denied: dict = {"error": "permission_denied"}

device_does_not_exist: dict = {"error": "this_device_does_not_exist"}

wallet_does_not_exist: dict = {"error": "this_wallet_does_not_exist"}

miner_does_not_exist: dict = {"error": "miner_does_not_exist"}

unknown_service: dict = {"error": "unknown_service"}

multiple_miners: dict = {"error": "there_is_an_miner_already_on_this_device"}

service_does_not_exist: dict = {"error": "service_does_not_exist"}

service_cannot_be_used: dict = {"error": "service_cannot_be_used"}

you_first_have_to_start_an_attack: dict = {"error": "you_first_have_to_start_an_attack"}

attack_scheme: dict = {
    "device_uuid": UUID(),
    "service_uuid": UUID(),
    "target_service": UUID(),
    "target_device": UUID()
}

standard_scheme: dict = {
    "device_uuid": UUID(),
    "service_uuid": UUID(),
}
