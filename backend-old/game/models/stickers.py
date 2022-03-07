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
            font-size: 40px;
            display: inline;
        }

        h2 {
            color: black;
            font-family: helvetica;
            font-size: 30px;
            display: inline;
        }

        .dashed {
            border-top: 2px dashed gray;
        }

        .sticker {
            padding: 1px;
        }

        .box {
            display: flex;
            align-items:center;
            padding: 0px;
            margin: 0px;
        }

        .line {
            height: 2px;
            border-width:0;
            color: gray;
            background-color: gray;
        }

        .desc {
            padding: 5px;
            font-family: helvetica;
            font-size: 20px;
        }

        ul {
            list-style-position: outside;
        }

        .image_container {
            display: flex;
            align-items:center;
            padding: 0px;
            margin: 0px;
            height: 310px;
            width: 310px;
            margin: 30px;
        }

        .vyroba {
            width: 50%;
            margin:10px auto;
        }

        .fit {
            max-width: 100%;
            max-height: 100%;
        }
    """

    def formatVyrobas(self, entity):
        vyrobas = entity.unlock_vyrobas.all()
        if not vyrobas:
            return ""
        fmt = '<div><b>Odemyká výrobu: </b>'
        labels = [vyroba.label for vyroba in vyrobas]
        fmt += ", ".join(labels)
        return fmt + '</div>'

    def formatEnhancers(self, entity):
        enhancers = entity.unlock_enhancers.all()
        if not enhancers:
            return ""
        fmt = '<div><b>Odemyká vylepšení:</b><br>'
        fmt += "<ul>"
        for enhancer in enhancers:
            enhancer_format  = f"{enhancer.label} ({enhancer.vyroba.label})"
            labels = [f"<li><b>{enhancer_format}: </b></li> {enhancer.dots} × {enhancer.die.label} &#x1f3b2;"]
            labels += [f"{res.amount} × {self.resource(res.resource)}" for res in enhancer.deploy_inputs.all()]
            fmt += ", ".join(labels)
            fmt += f"<br><em> + {enhancer.amount} × {self.resource(enhancer.vyroba.output)}</em>"
        fmt += "</ul>"
        return fmt + '</div>'

    def formatHeader(self, entity):
        if isinstance(entity, VyrobaModel) and entity.tech.island:
            code = self.getQRCode(entity.id)
        else:
            code = self.getQRCode(self.team.id + " " + entity.id)
        fmt = '<div class="box">'
        fmt += f'<img src="{code}" width="120" height="120">'
        fmt += f'<h1>{entity.label}</h1>'
        fmt += '</div>'
        return fmt

    def formatSharedHeader(self, entity):
        hex_path = os.path.join(os.getcwd(), "./game/data/icons/flag-hex.png")
        fmt = '<div class="box">'
        fmt += f'<img src="{hex_path}" width="120" height="120">'
        fmt += f'<h1>{entity.label}</h1>'
        fmt += '</div>'
        return fmt

    def formatTechs(self, entity):
        edges = entity.unlocks_tech.all()
        if not edges:
            return ""
        fmt = '<div><b>Navazující směry bádání:</b><ul>'
        for edge in edges:
            labels = [f'<li><b>{edge.dst.label}: </b>{edge.dots} × {edge.die.label} &#x1f3b2;']
            labels += [f'{res.amount} × {self.resource(res.resource)}' for res in edge.resources.all()]
            fmt += '<div>' + ', '.join(labels) + '</div>'
            fmt += '</li>'
        return fmt + '</ul></div>'

    def formatTechInfo(self, entity):
        vyrobas = self.formatVyrobas(entity)
        enhancers = self.formatEnhancers(entity)
        techs = self.formatTechs(entity)

        fmt = ""
        if entity.island:
            fmt += '<div class="desc">'
            fmt += f"Patří k ostrovu {entity.island.label} (obr +{entity.defenseBonus})"
            fmt += '</div>'
            fmt += '<hr class="line">'
        if vyrobas:
            fmt += '<div class="desc">'
            fmt += vyrobas
            fmt += '</div>'
            fmt += '<hr class="line">'
        if enhancers:
            fmt += '<div class="desc">'
            fmt += enhancers
            fmt += '</div>'
            fmt += '<hr class="line">'
        if techs:
            fmt += '<div class="desc">'
            fmt += techs
            fmt += '</div>'
            fmt += '<hr class="line">'
        return fmt

    def techTemplate(self, entity, header):
        fmt = '<hr class="dashed">'
        fmt += '<div class="sticker" vertical-align:top>'
        fmt += header
        fmt += '<hr class="line">'
        fmt += self.formatTechInfo(entity)
        fmt += f'<em>{entity.flavour}</em>'
        fmt += '</div>'
        return fmt

    def regularTechTemplate(self, entity):
        header = f'<div>{self.formatHeader(entity)}</div>'

        if entity.island:
            header += f'<div><h2>Ostrov: {entity.island.label}</h2></div>'

        return self.techTemplate(entity, header)

    def sharedTechTemplate(self, entity):
        header = self.formatSharedHeader(entity)
        return self.techTemplate(entity, header)

    def compactTechTemplate(self, entity):
        header = self.formatHeader(entity)
        fmt = '<hr class="dashed">'
        fmt +=  f'<div class="sticker">{header}</div>'
        return fmt

    def resource(self, resource):
        if resource.isProduction:
            return f'<u>{resource.label.replace("Produkce: ", "")}</u>'
        return resource.label

    def formatVyrobaInfo(self, entity):
        from game.models.actions.vyroba import vyrobaEnhanced
        originalEntity = entity
        entity = vyrobaEnhanced(self.state, self.team, entity)
        # Místo
        fmt = '<div class="desc">'
        fmt += f'<b>Probíha v:</b> {entity.build.label}'
        if originalEntity.tech.island:
            fmt += f' na ostrově {entity.tech.island.label}'
        fmt += '</div>'
        fmt += '<hr class="line">'
        # Vstupy
        fmt += '<div class="desc">'
        fmt += '<b>Vstupy:</b>'
        fmt += '<ul>'
        fmt += f'<li>{entity.dots} × {entity.die.label} &#x1f3b2;</li>'
        for resource, amount in entity.inputs.items():
            fmt += f'<li>{amount} × {self.resource(resource)}</li>'
        fmt += f'</ul>'
        fmt += '</div>'
        fmt += '<hr class="line">'
        # Výstup
        fmt += '<div class="desc">'
        fmt += f'<b>Výstup:</b> {entity.amount} × {self.resource(entity.output)}'
        fmt += '</div>'

        return fmt

    def regularVyrobaTemplate(self, entity):
        fmt = '<hr class="dashed">'
        fmt += '<div class="sticker" vertical-align:top>'
        fmt += self.formatHeader(entity)
        fmt += '<hr class="line">'
        fmt += self.formatVyrobaInfo(entity)
        fmt += '</div>'
        return fmt

    def renderBuildingImage(self, entity):
        path = os.path.join(os.getcwd(), f"./game/data/build/{entity.id}.png")
        move = 100 if entity.id != "build-hut" else 50
        fmt  = f'<div class="image_container" style="transform: translate(0,-{move}px)">'
        fmt += f'<img class="fit" src="{path}">'
        fmt += '</div>'
        return fmt

    def renderVyrobaImage(self, entity):
        if entity.output.icon and entity.output.icon != "-":
            name = entity.output.icon
            if entity.id.endswith("-mat"):
                name = name.replace("-a.svg", "-b.svg")
            path = os.path.join(os.getcwd(), f"./game/data/icons/{name}")
            fmt = '<div class="image_container">'
            fmt += '<div class="vyroba">'
            if self.entity.id not in ["vyr-cesta", "vyr-silnice"]:
                fmt += f'<img class="fit" src="{path}">'
            fmt += '</div>'
            fmt += '</div>'
            return fmt
        return ""

    def stickerType(self):
        return {
            StickerType.REGULAR: "Obyčejná",
            StickerType.SHARED: "Do stromu",
            StickerType.COMPACT: "Malá"
        }[self.type]

    def shortDescription(self):
        """
        Return a pretty short string description of the sticker
        """
        return f"{self.entity.label} pro {self.team.name} ({self.stickerType()})"

    def stickerName(self) -> str:
        return f"sticker_{self.id:04}_t{self.type.name}_s{self.state.id}"

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
        from game.models.state import State
        self.state = State.objects.get(id=self.state.id)
        self.state.setContext(self.state.action.action.context)
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

    def renderHTML(self, html, width, height):
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
        if self.type == StickerType.COMPACT:
            return self.renderBuildingCompact(entity)
        elif self.type == StickerType.SHARED:
            return self.renderBuildingShared(entity)
        else:
            return self.renderBuildingRegular(entity)

    def renderVyroba(self, entity):
        html = self.regularVyrobaTemplate(entity)
        html += self.renderVyrobaImage(entity)
        return self.renderHTML(html, 384, 768)

    def renderTechCompact(self, entity):
        html = self.compactTechTemplate(entity)
        return self.renderHTML(html, 384, 150)

    def renderTechRegular(self, entity):
        html = self.regularTechTemplate(entity)
        return self.renderHTML(html, 384, 768)

    def renderTechShared(self, entity):
        html = self.sharedTechTemplate(entity)
        return self.renderHTML(html, 384, 768)

    def renderBuildingCompact(self, entity):
        html = self.compactTechTemplate(entity)
        return self.renderHTML(html, 384, 150)

    def renderBuildingRegular(self, entity):
        html = self.regularTechTemplate(entity)
        html += self.renderBuildingImage(entity)
        return self.renderHTML(html, 384, 768)

    def renderBuildingShared(self, entity):
        html = self.sharedTechTemplate(entity)
        html += self.renderBuildingImage(entity)
        return self.renderHTML(html, 384, 768)


