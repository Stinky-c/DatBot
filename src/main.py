import asyncio

from helper import CogLoadingFailure, DatBot, MissingCogMeta, Settings


async def main():
    bot = DatBot.from_settings(Settings)
    for cog in Settings.bot.cogs:
        # fetch extension metadata
        try:
            meta = bot.load_extension_meta(cog)

        except MissingCogMeta:
            bot.clog.error(f"Missing metadata: '{cog}'")
            continue
        except CogLoadingFailure as e:
            bot.clog.error(e)
        except Exception as e:
            bot.clog.exception(f"Unknown error: {cog}", e)

        else:
            # requirement checks
            if meta.skip:
                bot.clog.info(f"Skipping '{meta.name}'")
                continue

            if meta.require_key and meta.key not in Settings.keys:
                bot.clog.error(f"Missing api key: {cog}")
                continue

            bot.load_extension(cog)
            bot.clog.info(f"Found '{meta.name}'")

    await bot.start(Settings.token.get_secret_value())


if __name__ == "__main__":
    asyncio.run(main())
