# Datbot

A crude selfhosted discord bot

## Notes

Alpha version.

More work features and functions coming later.

## TODO

- Change to use a CLI
- A better starting method

## Quick Start

1. Install [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/)
1. Copy [`config.example.toml`](config.example.toml) and rename to `config.toml`
1. Create `application.yml` and copy the [lavalink config](https://github.com/freyacodes/Lavalink/blob/master/LavalinkServer/application.yml.example) to it
1. Modify `docker-compose.yaml` and set the bot token
1. Run `docker-compose -d up`
