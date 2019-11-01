import app


# noinspection PyUnresolvedReferences
def load_endpoints():
    import resources.service
    import resources.miner
    import resources.bruteforce


if __name__ == "__main__":
    load_endpoints()
    app.m.run()
