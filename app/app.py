from cryptic import MicroService, Config, DatabaseWrapper

m: MicroService = MicroService("service")

wrapper: DatabaseWrapper = m.get_wrapper()
