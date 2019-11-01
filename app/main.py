import app


if __name__ == "__main__":

    # noinspection PyUnresolvedReferences
    from resources.service import *
    from resources.miner import *
    from resources.bruteforce import *

    app.wrapper.Base.metadata.create_all(bind=wrapper.engine)
    app.m.run()
