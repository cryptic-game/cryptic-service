# In game specific stuff

config: dict = {
    "CHANCE": 20000,

    "services": {
        "ssh": {
            "default_port": 22,
            "exploit_able": True,
            "allow_remote_access": True,
        },
        "brute4ce": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
        },
        "portscan": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
        },
        "telnet": {
            "default_port": 23,
            "exploit_able": True,
            "allow_remote_access": True,
        }
    }
}
