# In game specific stuff

config: dict = {
    "CHANCE": 20,
    "services": {
        "ssh": {
            "default_port": 22,
            "exploit_able": True,
            "allow_remote_access": True,
            "auto_start": True,
            "needs": {"cpu": 100, "ram": 100, "gpu": 100, "disk": 100, "network": 100},
        },
        "telnet": {
            "default_port": 23,
            "exploit_able": True,
            "allow_remote_access": True,
            "auto_start": True,
            "needs": {"cpu": 100, "ram": 100, "gpu": 100, "disk": 100, "network": 100},
        },
        "portscan": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "auto_start": False,
            "needs": {"cpu": 100, "ram": 100, "gpu": 100, "disk": 100, "network": 100},
        },
        "bruteforce": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "auto_start": False,
            "needs": {"cpu": 100, "ram": 100, "gpu": 100, "disk": 100, "network": 100},
        },
        "miner": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "auto_start": False,
            "needs": {"cpu": 100, "ram": 100, "gpu": 100, "disk": 100, "network": 100},
        },
    },
}
