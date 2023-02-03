import asyncio

from helper import DatBot, Settings, CogLoadingFailure


async def main():

    bot = DatBot.from_settings(Settings)
    for cog in Settings.bot.cogs:
        try:
            bot.load_extension(cog)
            bot.log.info(f"{cog} loaded")
        except CogLoadingFailure as e:
            bot.log.error(f"'{cog}' failed: {e}")
        except Exception as e:
            bot.log.error(f"Loading '{cog}' Failed : {e}")

    await bot.start(Settings.token.get_secret_value())


if __name__ == "__main__":
    asyncio.run(main())
