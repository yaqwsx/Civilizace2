if __name__ == "__main__":
    import django
    django.setup()

import contextlib
import os
from pathlib import Path
from collections.abc import Generator
from typing import List, Optional

import qrcode
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont, ImageOps
from backend.settings import ICON_PATH
from core.models.team import Team

from game.entities import Building, Entity, Tech, Vyroba
from game.models import DbEntities, DbSticker, StickerType
from game.util import FileCache

FONT_NORMAL = ImageFont.truetype(os.path.join(
    settings.DATA_PATH, "fonts", "Roboto-Regular.ttf"), 20)
FONT_BOLD = ImageFont.truetype(os.path.join(
    settings.DATA_PATH, "fonts", "Roboto-Bold.ttf"), 20)
FONT_HEADER = ImageFont.truetype(os.path.join(
    settings.DATA_PATH, "fonts", "Roboto-Bold.ttf"), 30)


def makeQrCode(content: str, pixelSize: int=3, borderQrPx: int=4) -> Image.Image:
    qr = qrcode.QRCode(
        error_correction=qrcode.ERROR_CORRECT_H,
        box_size=pixelSize,
        border=borderQrPx,
    )
    qr.add_data(content)
    qr.make(fit=True)

    return qr.make_image(fill_color="black", back_color="white").get_image()


class StickerBuilder:
    def __init__(self, width, xMargin: int=5, yMargin: int=20):
        self.img = Image.new("RGB", (width, 10 * width), color=(255, 255, 255))
        self.xMargin = xMargin
        self.yMargin = yMargin
        self.offset = 0
        self.yPosition = self.yMargin
        self.drawInt = ImageDraw.Draw(self.img)

    def _breakIntoLines(self, text: str, font: ImageFont.FreeTypeFont) -> List[str]:
        # Let's do it in a stupid way. TBA optimize
        words = text.split(" ")
        lines = []
        last = 0
        for i in range(1, len(words) + 1):
            l = " ".join(words[last: i])
            box = self.drawInt.textbbox(xy=(self.xMargin + self.offset, 0), text=l, font=font)
            if box[2] > self.img.width - self.xMargin:
                # If we cannot fit a single word on a line, just overflow it
                if last == i - 1:
                    i += 1
                lines.append(" ".join(words[last: i - 1]))
                last = i - 1
        lines.append(" ".join(words[last:]))
        return lines

    def addText(self, text, font) -> None:
        for line in self._breakIntoLines(text, font):
            box = self.drawInt.textbbox(
                xy=(self.xMargin + self.offset, self.yPosition),
                text=line,
                font=font,
            )
            self.drawInt.text(
                xy=(self.xMargin + self.offset, self.yPosition),
                text=line,
                font=font,
                anchor="la",
                align="left",
                fill=(0,0,0))
            self.yPosition = box[3]

    def addBulletLine(self, bullet, text, font, bulletFont=None) -> int: # bullet offset
        if bulletFont is None:
            bulletFont = font
        bulletBox = self.drawInt.textbbox(
            xy=(self.xMargin + self.offset, self.yPosition),
            text=bullet,
            font=bulletFont
        )
        # Draw bullet:
        self.drawInt.text(
            xy=(self.xMargin + self.offset, self.yPosition),
            text=bullet,
            font=bulletFont,
            anchor="la",
            align="left",
            fill=(0,0,0))
        with self.withOffset(bulletBox[2] - self.xMargin):
            self.addText(text, font)
        return bulletBox[2]

    @contextlib.contextmanager
    def withOffset(self, offset: int) -> Generator[None, None, None]:
        oldOffset = self.offset
        self.offset = offset
        try:
            yield None
        finally:
           self.offset = oldOffset

    def skip(self, offset: int) -> None:
        self.yPosition += offset

    def hline(self, width: int=4, margin: int=0) -> None:
        self.drawInt.line([(self.xMargin + margin, self.yPosition),
                           (self.img.width - self.xMargin - margin, self.yPosition)],
                           fill=(0, 0, 0), width=width, joint="curve")
        self.yPosition += width

    def addIcon(self, iconfile) -> None:
        """
        Given iconfilename adds icon at the current position in the middle
        """
        with Image.open(ICON_PATH / iconfile) as icon:
            newImg = icon.convert("1")
            xOffset = (self.img.width - icon.width) // 2
            self.img.paste(newImg, (xOffset, self.yPosition))
            self.yPosition += icon.height

    def getImage(self, height: Optional[int]=None) -> Image.Image:
        if height is None:
            bbox = ImageOps.invert(self.img).getbbox()
            assert bbox is not None, "Image is empty"
            height = bbox[3] + self.yMargin
        return self.img.crop((0, 0, self.img.width, height))

    def getTextSize(self, text, font):
        return self.drawInt.textbbox(xy=(0, 0),text=text, font=font)

def makeSticker(e: Entity, t: Team, stype: StickerType) -> Image.Image:
    if isinstance(e, Tech):
        return makeTechSticker(e, t, stype)
    if isinstance(e, Vyroba):
        return makeVyrobaSticker(e, t, stype)
    if isinstance(e, Building):
        return makeBuildingSticker(e, t, stype)
    assert False, f"There is no recipe for making {type(e)} stickers"

def underline(string):
    s = ""
    for x in string:
        s = f"{s}{x}\u0332"
    return s

def mm2Pt(mm: float) -> int:
    return int(mm / 25.4 * 180)

def getDefaultStickerBuilder() -> StickerBuilder:
    return StickerBuilder(mm2Pt(80), int((mm2Pt(80) - mm2Pt(53)) // 2))

def makeStickerHeader(e: Entity, t: Optional[Team], builder: StickerBuilder, first: bool=False) -> None:
    builder.hline(3, 0)
    builder.skip(5)

    if t is not None:
        code = f"{t.id} {e.id}"
    else:
        code = f"{e.id}"
    qr = makeQrCode(code, pixelSize=3, borderQrPx=4)

    builder.img.paste(qr, (builder.offset + builder.xMargin - 12, builder.yPosition))
    qrBottom = builder.yPosition + qr.height
    builder.skip(12)
    with builder.withOffset(qr.width):
        builder.addText(e.name, FONT_HEADER)
        if t is not None:
            builder.skip(5)
            if first:
                builder.addText(f"{t.name} vyzkoumali první", FONT_BOLD)
            else:
                builder.addText(f"({t.name})", FONT_NORMAL)
    builder.yPosition = max(builder.yPosition, qrBottom) + 10
    builder.hline(3, 0)
    builder.skip(5)

def makeStickerFooter(e: Entity, builder: StickerBuilder) -> None:
    builder.skip(40)
    builder.hline(3, 0)

def sortedCost(items):
    def keyFn(item):
        r, a = item
        idx = 10
        if r.id == "res-prace":
            idx = 0
        if r.typ is not None and r.typ[0].id == "typ-obchod":
            idx = 1
        return (idx, r.name)
    return sorted(items, key=keyFn)

def resourceName(resource):
    n = resource.name.replace(" ", " ")
    # TODO: replace with `isProduction`
    if resource.id.startswith("pro-") or resource.id.startswith("pge-"):
        return underline(n)
    return n

def makeTechSticker(e: Tech, team: Team, stype: StickerType) -> Image.Image:
    b = getDefaultStickerBuilder()
    makeStickerHeader(e, team, b, first=stype == StickerType.techFirst)

    if stype == StickerType.techSmall:
        return b.getImage()

    if len(e.flavor) > 0:
        b.addText(e.flavor, FONT_NORMAL)

    uVyrobas = e.unlocksVyrobas
    if len(uVyrobas) > 0:
        vText = ", ".join([v.name for v in uVyrobas])
        b.addText(f"Umožňuje: ", FONT_BOLD)
        b.addText(vText, FONT_NORMAL)
        b.skip(10)

    uBuildings = e.unlocksBuilding
    if len(uBuildings) > 0:
        bText = ", ".join([v.name for v in uBuildings])
        b.addText(f"Je možné stavět: ", FONT_BOLD)
        b.addText(bText, FONT_NORMAL)
        b.skip(10)

    bulletWidth = b.getTextSize(text="• ", font=FONT_NORMAL)[2]

    uTechs = sorted(e.unlocksTechs, key=lambda x: x.name)
    if len(uTechs) > 0:
        b.skip(5)
        b.addText("Odemyká směry bádání:", FONT_BOLD)
        with b.withOffset(10):
            for t in uTechs:
                costText = ", ".join([f"{a}× {resourceName(r)}" for r, a in sortedCost(t.cost.items())])
                diceText = f"Kostka: {t.points}× {', '.join(d.briefName for d in e.allowedDie(t))}"
                b.addText(f"• {t.name}: ", FONT_BOLD)
                with b.withOffset(b.offset + bulletWidth):
                    b.addText(diceText, FONT_NORMAL)
                    b.addText(costText, FONT_NORMAL)

    makeStickerFooter(e, b)
    return b.getImage(mm2Pt(95))

def makeBuildingSticker(e: Building, t: Team, stype: StickerType) -> Image.Image:
    assert stype == StickerType.regular

    b = getDefaultStickerBuilder()
    makeStickerHeader(e, t, b)

    featureText = ", ".join([f.name for f in e.requiredFeatures])
    if len(featureText) > 0:
        b.addBulletLine("Vyžaduje: ", featureText, FONT_NORMAL, bulletFont=FONT_BOLD)
    b.addBulletLine("Kostka: ", f"{e.points}", FONT_NORMAL, FONT_BOLD)
    b.addText("Cena:", FONT_BOLD)
    with b.withOffset(10):
        for r, a in sortedCost(e.cost.items()):
            b.addBulletLine("• ", f"{a}× {resourceName(r)}", FONT_NORMAL)

    icon = e.icon
    if icon is not None:
        icon = os.path.splitext(icon)[0] + "-lg.png"
        b.skip(10)
        try:
            b.addIcon(icon)
        except Exception:
            pass

    makeStickerFooter(e, b)

    return b.getImage()

def makeVyrobaSticker(e: Vyroba, t: Team, stype: StickerType) -> Image.Image:
    assert stype == StickerType.regular

    b = getDefaultStickerBuilder()
    makeStickerHeader(e, t, b)

    if len(e.flavor) > 0:
        b.addText(e.flavor, FONT_NORMAL)

    featureText = ", ".join([f.name for f in e.requiredFeatures])
    b.addBulletLine("Kostka: ", f"{e.points}", FONT_NORMAL, FONT_BOLD)
    if len(featureText) > 0:
        b.addBulletLine("Vyžaduje: ", featureText, FONT_NORMAL, bulletFont=FONT_BOLD)
    b.skip(5)
    b.addText("Vstupy:", FONT_BOLD)
    with b.withOffset(10):
        for r, a in sortedCost(e.cost.items()):
            b.addBulletLine("• ", f"{a}× {resourceName(r)}", FONT_NORMAL)

    rRes = e.reward[0]
    b.addBulletLine("Výstup: ", f"{e.reward[1]}× {resourceName(rRes)}", FONT_NORMAL,
        bulletFont=FONT_BOLD)

    icon = rRes.icon
    if icon is not None:
        icon = os.path.splitext(icon)[0] + "-md.png"
        try:
            b.addIcon(icon)
        except Exception:
            pass

    makeStickerFooter(e, b)
    return b.getImage()

STICKER_CACHE = FileCache(settings.CACHE / "stickers", ".png")

def getStickerFile(stickerModel: DbSticker) -> Path:
    _, entities = DbEntities.objects.get_revision(stickerModel.entityRevision)
    def render(path):
        s = makeSticker(entities[stickerModel.entityId], stickerModel.team, stickerModel.stickerType)
        s.save(path)
    return STICKER_CACHE.path(stickerModel.ident, render)

if __name__ == "__main__":
    from game.tests.actions.common import TEST_ENTITIES
    team_zeleni = Team.objects.model(id="tea-zeleni", name="Zelení", color="green")

    vyroba = makeSticker(TEST_ENTITIES["vyr-drevo1Pro"], team_zeleni, StickerType.regular)
    # vyroba.show()
    tech = makeSticker(TEST_ENTITIES["tec-start"], team_zeleni, StickerType.regular)
    tech.show()
    tech.save("test.png")
