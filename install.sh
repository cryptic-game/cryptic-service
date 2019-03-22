#!/bin/bash
set -ex
docker-compose pull
docker-compose up -d
cd app
pip3 install git+https://github.com/cryptic-game/python3-lib.git