# Datbot

A crude selfhosted discord bot

## Features

- CurseForge search
- Complex calculator
- Sandboxed code execution
- Pin channel

## Status

Beta version.

More work features and functions coming later.

## TODO

- Finish music
- Fix watchdog
    - not watching helper
- Document current cogs
- More diverse and complex ideas
- Manual blacklisting/whitelisting of cogs
    - Docker integration?
    - 'itzg/docker-minecraft-server` cog?
        - Spin up of configured container?
        - manage docker-compose file?
- Fool proof documentation
- Public release?

## Cog dependent TODO'S

- Custom AST parser for math cog
    - Typeable on normal keyboard
    - Better symbols
    - defining variables and functions
    - Tests and testing

## Quick Start

1. Install [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/)
1. Copy [`config.example.toml`](config.example.toml) and rename to `config.toml` changing values as needed
1. Create `application.yml` and copy the [lavalink config](https://github.com/freyacodes/Lavalink/blob/master/LavalinkServer/application.yml.example) to it
1. Modify `docker-compose.yaml` and set the bot token
1. Run `docker-compose -d up` to start and `docker-compose down` to shutdown

## Notes

Lavalink can only be ran on x86 due to the limitation set by lavalink. There are [alternate builds](https://github.com/Cog-Creators/Lavalink-Jars/releases) for other architectures, but support will not be provided
