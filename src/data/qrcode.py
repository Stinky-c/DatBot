import disnake
from qrcode.image.styles.moduledrawers import (
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer,
)
from qrcode.image.styles.colormasks import (
    RadialGradiantColorMask,
    SquareGradiantColorMask,
    HorizontalGradiantColorMask,
    ImageColorMask,
    VerticalGradiantColorMask,
)
from qrcode.image.styledpil import (
    SquareModuleDrawer,
    SolidFillColorMask,
)
from qrcode.constants import (
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_H,
    ERROR_CORRECT_Q,
)

# fmt: off
__all = disnake.Embed.from_dict({"fields": [{"inline": False,"name": "Arugments","value": "Requirements or options applying to all commands except special cases",},{"inline": False,"name": "Data:","value": "Data is a a string passed as an arugment",},{"inline": False,"name": "Files","value": "File is uploaded to discords cdn and code redirects to a link",},{"inline": False,"name": "Error Correction","value": " an optional percentage value of the codes error correction",},{"inline": False,"name": "Resources:","value": "Websites Providing info",},{"inline": True,"name": "Beaconstac","value": "https://www.beaconstac.com/what-is-qr-code",},{"inline": True,"name": "Wikipedia","value": "https://en.wikipedia.org/wiki/QR_code",},],"color": disnake.Color.random(),"type": "rich","description": "Mode: All","title": "QR Code help",})
__auto = disnake.Embed.from_dict({"fields": [{"inline": False,"name": "Fucntion:","value": "Auto generates a simple code from the given data without much configuration",},{"inline": True, "name": "Required:", "value": "Data or a file"},],"color": disnake.Color.random(),"type": "rich","description": "Mode: Auto","title": "QR Code help",})
__stylized = disnake.Embed.from_dict({"fields": [{"inline": False,"name": "Function:","value": "Generates a stylized code from the given data using the provided configuration",},{"inline": True, "name": "Required:", "value": "Data or a file"},{"inline": True,"name": "Options:","value": "bg and fg colors formatted in comma sepertaed RGB values",},{"inline": True, "name": "Optional:", "value": "error correction margin"},],"color": disnake.Color.random(),"type": "rich","description": "Mode: Stylized","title": "QR Code help",})
__ascii = disnake.Embed.from_dict({"fields": [{"inline": False,"name": "Function:","value": "Generates an ascii code from the given data",},{"inline": True, "name": "Required:", "value": "Data or a file"},{"inline": True,"name": "as_file:","value": "Uploads as a file instead of a codeblock",},{"inline": True, "name": "Optional:", "value": "error correction margin"},],"color": disnake.Color.random(),"type": "rich","description": "Mode: Ascii","title": "QR Code help",})
__svg = disnake.Embed.from_dict({"fields": [{"inline": False,"name": "Function:","value": "Generates a SVG code from the given data",},{"inline": True,"name": "Required:","value": "Data or a file",},{"inline": True, "name": "Optional:", "value": "error correction margin"},],"color": disnake.Color.random(),"type": "rich","description": "Mode: SVG","title": "QR Code help",})
emebedHelp = {"All":__all,"Auto":__auto,"Stylized":__stylized,"Ascii":__ascii,"SVG":__svg}

moddrawer = {"Square Data": SquareModuleDrawer,"Gapped Square Data": GappedSquareModuleDrawer,"Circle Data": CircleModuleDrawer,"Rounded Data": RoundedModuleDrawer,"Vertical Bars Data": VerticalBarsDrawer,"Horizontal Bars Data": HorizontalBarsDrawer,}
colormasks = {"SolidFillColorMask":SolidFillColorMask,"RadialGradiantColorMask":RadialGradiantColorMask,"SquareGradiantColorMask":SquareGradiantColorMask,"HorizontalGradiantColorMask":HorizontalGradiantColorMask,"VerticalGradiantColorMask":VerticalGradiantColorMask,"ImageColorMask":ImageColorMask}
errorCorrectionLevel={"7%":ERROR_CORRECT_L,"15%":ERROR_CORRECT_M,"25%":ERROR_CORRECT_Q,"30%":ERROR_CORRECT_H,}
