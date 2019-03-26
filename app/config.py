import os
from typing import Union, Tuple

to_load: Union[str, Tuple[str, bool]] = [
    ("storage_location", None)
]

# the final configuration dict
config: dict = {}

# load all configuration values from the env
for key in to_load:
    if isinstance(key, tuple):
        if key[0] in os.environ:
            config[key[0]] = os.environ.get(key[0])
        else:
            config[key[0]] = key[1]
    elif key in os.environ:
        config[key] = os.environ.get(key)

if config["storage_location"] is None: # Just in case
    config["storage_location"] = "./test_db.db"