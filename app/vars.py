# In game specific stuff

config: dict = {
    "CHANCE": 20,

    "services": {
        "ssh": {
            "default_port": 22,
            "exploit_able": True,
            "allow_remote_access": True,
            "auto_start": True,
            "consumption": 100,
        },
        "telnet": {
            "default_port": 23,
            "exploit_able": True,
            "allow_remote_access": True,
            "auto_start": True,
            "consumption": 50,
        },
        "portscan": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "auto_start": False,
            "consumption": 500,
        },
        "bruteforce": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "auto_start": False,
            "consumption": 1000,
        },
        "miner": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "auto_start": False,
            "consumption": 5000
        }
    }
}
