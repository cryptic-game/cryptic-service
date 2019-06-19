from cryptic import MicroService, Config, DatabaseWrapper, get_config

config: Config = get_config()  # / production

m: MicroService = MicroService('service')

wrapper: DatabaseWrapper = m.get_wrapper()

if __name__ == '__main__':
    # noinspection PyUnresolvedReferences
    from resources.service import *
    from resources.miner import *
    from resources.bruteforce import *

    wrapper.Base.metadata.create_all(bind=wrapper.engine)
    m.run()
