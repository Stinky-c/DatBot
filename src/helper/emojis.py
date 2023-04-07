from enum import StrEnum


class Emojis(StrEnum):
    """A small enum with emojis"""

    thumbs_up = "👍"
    thumbs_down = "👎"
    wave = "👋"
    skull = "💀"
    checkmark = "✅"
    cross = "❌"
    x = cross
    arrow_left = "⬅️"
    arrow_right = "➡️"

    # Custom
    github = "<:GitHubMarkLight32px:1019046766345191444>"
    git_vsc = "<:git_vsc:1019057811017191555>"
    meowdy = "<:meowdy:851473163362631691>"
    download = "<:download_arrow:1091520127738069044>"


class CurseforgeEmojis(StrEnum):
    addons = "<:cf_addons:1093665805645905952>"
    size = "<:cf_size:1093665810783940698>"
    download = "<:cf_download:1093665808686788639>"
    created = "<:cf_created:1093665807260713012>"
    uploaded = "<:cf_uploaded:1093665812738486392>"
    updated = "<:cf_updated:1093667691035893760>"
