from scheme import UUID

invalid_request: dict = {"error": "invalid_request"}

success_scheme: dict = {"ok": True}

multiple_services: dict = {"error": "you_already_own_a_service_with_this_name"}

service_is_not_supported: dict = {"error": "this_service_is_not_supported"}

permission_denied: dict = {"error": "permission_denied"}

device_does_not_exist: dict = {"error": "this_device_does_not_exist"}

wallet_does_not_exist: dict = {"error": "this_wallet_does_not_exist"}

miner_does_not_exist: dict = {"error": "miner_does_not_exist"}

unknown_service: dict = {"error": "unknown_service"}

multiple_miners: dict = {"error": "there_is_an_miner_already_on_this_device"}

service_does_not_exists: dict = {"error": "service_does_not_exists"}

default_required: dict = {
    "device_uuid": UUID(),
    "service_uuid": UUID()
}
