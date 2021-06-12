from game.data.tech import TechModel
from game.data.vyroba import VyrobaModel
from django.db import models
from django_enumfield import enum
from game.data.entity import EntityModel
from game.data.tech import TechModel
from game.data.vyroba import VyrobaModel

from html2image import Html2Image

import tempfile
import qrcode

from PIL import Image, ImageDraw
import io
import os
from pathlib import Path

class FileCache:
    def __init__(self, cacheDirectory, suffix):
        self.cacheDirectory = cacheDirectory
        Path(cacheDirectory).mkdir(exist_ok=True)
        self.suffix = suffix

    def name(self, ident):
        return f"{ident}.{self.suffix}"

    def path(self, ident, renderer):
        """
        Given an object ident (something convertible to string) and renderer
        (function that can render the object to bytes), return the path to rendered
        object. If object is not cached it will be rendered.
        """
        file = self.cacheFile(ident)
        if os.path.isfile(file):
            return file

        basedir = os.path.dirname(file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        content = renderer()
        with open(file, "wb") as f:
            f.write(content)
        return file

    def get(self, ident, renderer):
        """
        Given an object ident (something convertible to string) and renderer
        (function that can render the object to bytes), return the object either
        from cache or by rendering it.
        """
        file = self.cacheFile(ident)

        basedir = os.path.dirname(file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        try:
            with open(file, "rb") as f:
                return f.read()
        except FileNotFoundError:
            content = renderer()
            with open(file, "wb") as f:
                f.write(content)
            return content
    
    def cacheFile(self, ident):
        cwd = os.getcwd()
        return os.path.join(cwd, self.cacheDirectory, self.name(ident))

STICKER_CACHE_FOLDER = "./_stickers"
QRCODE_CACHE_FOLDER = "./_codes"

QRCODE_CACHE = FileCache(QRCODE_CACHE_FOLDER, "png")
STICKER_CACHE = FileCache(STICKER_CACHE_FOLDER, "png")

class StickerType(enum.Enum):
    REGULAR = 0
    SHARED = 1
    COMPACT = 2

class Sticker(models.Model):
    """
    Sticker model. The model is defined by an entity, team and a state.
    """
    entity = models.ForeignKey(EntityModel, on_delete=models.PROTECT, null=False)
    type = enum.EnumField(StickerType, default=StickerType.REGULAR)
    state = models.ForeignKey("State", on_delete=models.PROTECT, null=True)
    team = models.ForeignKey("Team", on_delete=models.PROTECT, null=True)
    awardedAt = models.DateTimeField("Time of creating the action", auto_now=True)

    cssstyle = """
        body { background-color: white; }
        h1 {
            color: black;
            font-family: helvetica;
            font-size: 50px;
            display: inline;
        }

        .sticker {
            padding: 2px;
        }

        .box {
            display: flex;
            align-items:center;
        }

        .line {
            height: 2px;
            border-width:0;
            color: gray;
            background-color: gray;
        }

        .desc {
            padding: 10px;
            font-family: helvetica;
            font-size: 25px;
        }

        .desc-title {
            padding: 10px;
            font-weight:    bold;
        }

        .desc-elem {
            padding: 10px;
        }
    """

    def formatVyrobas(self, entity):
        vyrobas = entity.unlock_vyrobas.all()
        if not vyrobas:
            return ""
        format = '<div><b>Odemyká výrobu:</b><ul>'
        for vyroba in vyrobas:
            format += f'<li>{vyroba.label}</li>'
        return format + '</ul></div>'

    def formatEnhancers(self, entity):
        enhancers = entity.unlock_enhancers.all()
        if not enhancers:
            return ""
        format = '<div><b>Odemyká vylepšení:</b><ul>'
        for enhance in enhancers:
            format += f'<li>{enhance.label}</li>'
        return format + '</ul></div>'

    def formatHeader(self, entity):
        code = self.getQRCode(entity.id)
    
        return """
            <div class="box">
                <img src="{1}" width="120" height="120">
                <h1>{0}</h1>
            </div>
        """.format(entity.label, code)

    def formatSharedHeader(self, entity):
        hex_path = os.path.join(os.getcwd(), "./img/flag-hex.png")
        print(os.getcwd())
        print(hex_path)
        return """
            <div class="box">
                <img src="{1}" width="120" height="120">
                <h1>{0}</h1>
            </div>
        """.format(entity.label, hex_path)

    def formatTechs(self, entity):
        techs = entity.unlocks_tech.all()
        if not techs:
            return ""
        format = '<div><b>Navazující směry bádání:</b><ul>'
        for tech in techs:
            format += f'<li>{tech.label}</li>'
        return format + '</ul></div>'

    def formatTechDescription(self, entity):
        vyrobas = self.formatVyrobas(entity)
        enhancers = self.formatEnhancers(entity)
        techs = self.formatTechs(entity)
        return f'<div class="desc">{vyrobas}{enhancers}{techs}</div>'

    def regularTechTemplate(self, entity):
        header = f'<div>{self.formatHeader(entity)}</div>'
        return self.techTemplate(entity, header)

    def sharedTechTemplate(self, entity):
        header = f'<div>{self.formatSharedHeader(entity)}</div>'
        return self.techTemplate(entity, header)

    def techTemplate(self, entity, header):
        desc = self.formatTechDescription(entity)

        return """
        <div class="sticker" vertical-align:top>
            {0}
            <hr class="line">
            {1}
            <em>{2}</em>
        </div>
        """.format(header, desc, entity.flavour)

    def compactTechTemplate(self, entity):
        header = self.formatHeader(entity)
        return f'<div class="sticker">{header}</div>'

    def shortDescription(self):
        """
        Return a pretty short string description of the sticker
        """
        return f"Sticker \nfor team {self.team.id} \nof {self.entity.id}"

    def stickerName(self) -> str:
        return f"sticker_{self.id:04d}_{self.type.name}" 

    def getImage(self):
        """
        Return sticker image as PNG file in bytes
        """
        return STICKER_CACHE.get(self.stickerName(), lambda: self.render())

    def getQRCode(self, text):
        """
        Return Path to generated QR Code
        """
        return QRCODE_CACHE.path(text, lambda: self.renderQRCode(text))

    def renderQRCode(self, text):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )

        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()

    def render(self):
        """
        Render the sticker into PNG file returned as bytes
        """
        choices = {
            "build-": (TechModel, self.renderBuilding),
            "tech-": (TechModel, self.renderTech),
            "vyr-": (VyrobaModel, self.renderVyroba)
        }
        for pref, (mod, ren) in choices.items():
            if self.entity.id.startswith(pref):
                return ren(mod.manager.get(pk=self.entity.pk))
        raise RuntimeError(f"Unknown entity type to render {self.entity.id}")

    def renderInternal(self):
        """
        Render the sticker into PNG file returned as bytes
        """
        img = Image.new('RGB', (100, 100), color = (255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((10,10), self.shortDescription(), fill=(0,0,0))
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()

    def renderHTML(self, html, width, height, rotate = False):
        """
        Render the sticker into PNG file returned as bytes
        """
        dir = tempfile.gettempdir()
        name = self.stickerName() + '.png'

        hti = Html2Image(size=(width, height))
        hti.output_path = dir
        hti.screenshot(
            html_str = html,
            css_str  = self.cssstyle,
            save_as  = name
        )

        path = os.path.join(dir, name)
        with Image.open(os.path.join(dir, name)) as img:
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer.getvalue()

    def renderTech(self, entity):
        if self.type == StickerType.COMPACT:
            return self.renderTechCompact(entity)
        elif self.type == StickerType.SHARED:
            return self.renderTechShared(entity)
        else: 
            return self.renderTechRegular(entity)

    def renderBuilding(self, entity):
        return self.renderInternal(entity)

    def renderVyroba(self, entity):
        return self.renderInternal(entity)

    def renderTechCompact(self, entity):
        html = self.compactTechTemplate(entity)
        return self.renderHTML(html, 384, 150)
    
    def renderTechRegular(self, entity):
        html = self.regularTechTemplate(entity)
        return self.renderHTML(html, 384, 610, True)

    def renderTechShared(self, entity):
        html = self.sharedTechTemplate(entity)
        return self.renderHTML(html, 384, 610, True)


