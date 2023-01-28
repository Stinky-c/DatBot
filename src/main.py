import asyncio


from helper import DatBot, Settings


async def main():

    bot = DatBot.from_settings(Settings)
    for cog in Settings.bot.cogs:
        bot.load_extension(cog)
        try:
            bot.log.info(f"{cog} loaded")
        except Exception:
            bot.log.error(f"Loading '{cog}' Failed")

    await bot.start(Settings.token.get_secret_value())


if __name__ == "__main__":
    asyncio.run(main())
