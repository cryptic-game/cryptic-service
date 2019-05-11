from cryptic import MicroService, Config, DatabaseWrapper, get_config

config: Config = get_config("production")  # / production

m: MicroService = MicroService('service')

wrapper: DatabaseWrapper = m.get_wrapper()

if __name__ == '__main__':
    from resources.service import *

    wrapper.Base.metadata.create_all(bind=wrapper.engine)
    m.run()
