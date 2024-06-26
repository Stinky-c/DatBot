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
- Spring cleaning
- Update Examples

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

## Configuring Minecraft Cog

### About

This is a very work in progress feature that will probably be detached into its own project in the future

### Requirements

- An available unix docker socket
- CurseForge api key
- A configured docker network
    - preferably named `mcserver`
- A Domain with wildcard CNAME's

### Configuration

Update `config.toml` with the following, updating values as needed

```toml
[keys.mcserver]
cfapikey = "< CurseForge API key>"      # The curseforge api key to support use of cf packs
routerUrl = "http://mcrouter:25564"     # An internal router to dispatch to dependent servers
hostUrl = "{name}.< Domain >"           # A partial fqdn to provision and point servers to
dockerNetwork = "< Docker Network >"    # Docker network name for newly created containers to join
```

## Notes

Lavalink can only be ran on x86 due to the limitation set by lavalink. There are [alternate builds](https://github.com/Cog-Creators/Lavalink-Jars/releases) for other architectures, but support will not be provided

Lavalink dropped native support for youtube; use [lavalink-devs/youtube-source](https://github.com/lavalink-devs/youtube-source) and add it to lavalink configuration as needed
