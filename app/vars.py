# In game specific stuff
import math
from typing import Tuple


def calculate_speed_miner(
    edata: Tuple[float, float, float, float, float], rdata: Tuple[float, float, float, float, float]
) -> float:
    cpu, ram, *_ = rdata
    return 0.0115 - (0.0115 - 0.006) * math.exp((-cpu * ram * (ram * cpu / 116_000 - 1)) / 58_000_000_000)


def calculate_speed_bruteforce(
    edata: Tuple[float, float, float, float, float], rdata: Tuple[float, float, float, float, float]
) -> float:
    return min(sum(rdata) / sum(edata), 1)


def standard_speed(
    edata: Tuple[float, float, float, float, float], rdata: Tuple[float, float, float, float, float]
) -> float:
    return min(sum(rdata) / sum(edata), 1)


config: dict = {
    "CHANCE": 20,
    "services": {
        "ssh": {
            "default_port": 22,
            "exploit_able": True,
            "allow_remote_access": True,
            "auto_start": True,
            "toggleable": False,
            "needs": {"cpu": 100, "ram": 100, "gpu": 100, "disk": 100, "network": 100},
            "speedm": standard_speed,
        },
        "telnet": {
            "default_port": 23,
            "exploit_able": True,
            "allow_remote_access": True,
            "auto_start": True,
            "toggleable": True,
            "needs": {"cpu": 100, "ram": 100, "gpu": 100, "disk": 100, "network": 100},
            "speedm": standard_speed,
        },
        "portscan": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "auto_start": False,
            "toggleable": False,
            "needs": {"cpu": 30, "ram": 20, "gpu": 0, "disk": 0, "network": 228},
            "speedm": standard_speed,
        },
        "bruteforce": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "auto_start": False,
            "toggleable": False,
            "needs": {"cpu": 50, "ram": 630, "gpu": 100, "disk": 10, "network": 243},
            "speedm": calculate_speed_bruteforce,
        },
        "miner": {
            "default_port": None,
            "exploit_able": False,
            "allow_remote_access": False,
            "auto_start": False,
            "toggleable": False,
            "needs": {"cpu": 1200, "ram": 112, "gpu": 24, "disk": 10, "network": 375},
            "speedm": calculate_speed_miner,
        },
    },
}
