cryptic-service
============

The official service microservice of Cryptic (https://cryptic-game.net/).

## Testing with pipenv

You can also test it without docker using pipenv:

`pipenv run dev` or `pipenv run prod`

To install the dependencies manually use:

`pipenv install`

If you only need a mysql-server you can bring it up with:

`docker-compose up -d db`

## Docker-Hub

This microservice is online on docker-hub (https://hub.docker.com/r/useto/cryptic-service/).

## API Documentation

Go here to read the [documentation](https://github.com/cryptic-game/cryptic-service/wiki)


|Endpoint       | Data              | Functionality |
|---------      | ----------        |-------------- |
|create         |                   | create new service
|public_info    |                   | public info about a given service
|private_info   |                   | private info about a given service
|turn           |                   | turns service on/off
|delete         |                   | deletes service
|list           |                   | lists services on device
|part_owner     |                   | checks if you temporary part owner of this service
|bruteforce     |                   | Bruteforce SSH
