# In game specific stuff

config: dict = {
    "CHANCE": 20,

    "services": {
        "ssh": {
            "default_port": 22,
            "exploit_able": True,
            "allow_remote_access": True,
            "consumption": 100,
        },
        "bruteforce": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "consumption": 1000,
        },
        "portscan": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "consumption": 500,
        },
        "telnet": {
            "default_port": 23,
            "exploit_able": True,
            "allow_remote_access": True,
            "consumption": 50,
        },
        "miner": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "consumption": 5000,
            "a": 1,
            "b": 800,
            "c": 512,

        }
    }
}
