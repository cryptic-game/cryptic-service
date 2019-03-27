# In game specific stuff

config: dict = {
    "CHANCE": 2,

    "services": {
        "SSH": {
            "exposed": True,
            "default_port": 22,
            "exploit_able": True,
            "allow_remote_access": True,
        },
        "Hydra": {
            "exposed": False,
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
        },
        "nmap": {
            "exposed": False,
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,

        },
        "Telnet": {
            "exposed": True,
            "default_port": 23,
            "exploit_able": True,
            "allow_remote_access": True,

        }
    }
}
