import asyncio

from helper import CogLoadingFailure, DatBot, Settings


async def main():

    bot = DatBot.from_settings(Settings)
    for cog in Settings.bot.cogs:
        try:
            bot.load_extension(cog)
            bot.log.info(f"{cog} loaded")
        except CogLoadingFailure as e:
            bot.log.error(f"'{cog}' failed")
            bot.log.exception(e)
        except Exception as e:
            bot.log.error(f"Loading '{cog}' Failed")
            bot.log.exception(e)

    await bot.start(Settings.token.get_secret_value())


if __name__ == "__main__":
    asyncio.run(main())
