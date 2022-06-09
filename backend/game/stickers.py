if __name__ == "__main__":
    import django
    django.setup()

import contextlib
import math
import os
from pathlib import Path
from typing import List, Optional

import qrcode
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont, ImageOps
from core.models.team import Team

from game.entities import Entity, Tech, Vyroba
from game.models import DbDelayedEffect, DbEntities, DbSticker, StickerType
from game.util import FileCache

FONT_NORMAL = ImageFont.truetype(os.path.join(
    settings.DATA_PATH, "fonts", "Roboto-Regular.ttf"), 22)
FONT_BOLD = ImageFont.truetype(os.path.join(
    settings.DATA_PATH, "fonts", "Roboto-Bold.ttf"), 22)
FONT_HEADER = ImageFont.truetype(os.path.join(
    settings.DATA_PATH, "fonts", "Roboto-Bold.ttf"), 30)


def makeQrCode(content: str, pixelSize: int=3, borderQrPx: int=4) -> Image:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=pixelSize,
        border=borderQrPx,
    )
    qr.add_data(content)
    qr.make(fit=True)

    return qr.make_image(fill_color="black", back_color="white").get_image()


class StickerBuilder:
    def __init__(self, width, margin: int=5):
        self.img = Image.new("RGB", (width, 10 * width), color=(255, 255, 255))
        self.margin = margin
        self.offset = 0
        self.position = self.margin
        self.drawInt = ImageDraw.Draw(self.img)

    def _breakIntoLines(self, text: str, font: ImageFont.FreeTypeFont) -> List[str]:
        # Let's do it in a stupid way. TBA optimize
        words = text.split(" ")
        lines = []
        last = 0
        for i in range(1, len(words) + 1):
            l = " ".join(words[last: i])
            box = self.drawInt.textbbox(xy=(self.margin + self.offset, 0), text=l, font=font)
            if box[2] > self.img.width - self.margin:
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
                xy=(self.margin + self.offset, self.position),
                text=line,
                font=font,
            )
            self.drawInt.text(
                xy=(self.margin + self.offset, self.position),
                text=line,
                font=font,
                anchor="la",
                align="left",
                fill=(0,0,0))
            self.position = box[3]

    def addBulletLine(self, bullet, text, font, bulletFont=None) -> int: # bullet offset
        if bulletFont is None:
            bulletFont = font
        bulletBox = self.drawInt.textbbox(
            xy=(self.margin + self.offset, self.position),
            text=bullet,
            font=bulletFont
        )
        # Draw bullet:
        self.drawInt.text(
            xy=(self.margin + self.offset, self.position),
            text=bullet,
            font=bulletFont,
            anchor="la",
            align="left",
            fill=(0,0,0))
        with self.withOffset(bulletBox[2] - self.margin):
            self.addText(text, font)
        return bulletBox[2]

    @contextlib.contextmanager
    def withOffset(self, offset: int) -> None:
        oldOffset = self.offset
        self.offset = offset
        try:
            yield None
        finally:
           self.offset = oldOffset

    def skip(self, offset: int) -> None:
        self.position += offset

    def hline(self, width: int=4, margin: int=0) -> None:
        self.drawInt.line([(self.margin + margin, self.position),
                           (self.img.width - self.margin - margin, self.position)],
                           fill=(0, 0, 0), width=width, joint="curve")
        self.position += width

    def getImage(self) -> Image:
        bbox = ImageOps.invert(self.img).getbbox()
        return self.img.crop((0, 0, self.img.width, bbox[3] + self.margin))

def makeSticker(e: Entity, t: Team, stype: StickerType) -> Image:
    if isinstance(e, Tech):
        return makeTechSticker(e, t, stype)
    if isinstance(e, Vyroba):
        return makeVyrobaSticker(e, t, stype)
    assert f"There is no recipe for making {type(e)} stickers"

def getDefaultStickerBuilder() -> StickerBuilder:
    # return StickerBuilder(396, 15)
    return StickerBuilder(int(80 // 25.4 * 180), int((80 / 25.4 * 180 - 396) // 2))

def makeStickerHeader(e: Entity, t: Optional[Team], builder: StickerBuilder) -> None:
    builder.hline(3, 0)
    builder.skip(100)
    builder.hline(3, 0)
    builder.skip(5)

    if t is not None:
        code = f"{t.id} {e.id}"
    else:
        code = f"{e.id}"
    qr = makeQrCode(code, pixelSize=3, borderQrPx=4)

    builder.img.paste(qr, (builder.offset + builder.margin - 12, builder.position))
    qrBottom = builder.position + qr.height
    builder.skip(12)
    with builder.withOffset(qr.width):
        builder.addText(e.name, FONT_HEADER)
    builder.position = max(builder.position, qrBottom) + 10
    builder.hline(1, 0)
    builder.skip(5)

def makeStickerFooter(e: Entity, builder: StickerBuilder) -> None:
    builder.skip(40)
    builder.hline(3, 0)

def makeTechSticker(e: Tech, t: Team, stype: StickerType) -> Image:
    b = getDefaultStickerBuilder()
    makeStickerHeader(e, t, b)

    if stype == StickerType.techSmall:
        makeStickerFooter(e, b)
        return b.getImage()

    uVyrobas = e.unlocksVyrobas
    if len(uVyrobas) > 0:
        vText = ", ".join([v.name for v in uVyrobas])
        b.addBulletLine("Umožňuje: ", vText, FONT_NORMAL, bulletFont=FONT_BOLD)

    uTechs = e.unlocksTechs
    if len(uTechs) > 0:
        b.skip(5)
        b.addText("Odemyká směry bádání:", FONT_BOLD)
        with b.withOffset(10):
            for t in uTechs:
                costText = ", ".join([f"{a}× {r.name}" for r, a in t.cost.items()])
                b.addBulletLine(f"• {t.name}: ", costText, FONT_NORMAL, bulletFont=FONT_BOLD)

    makeStickerFooter(e, b)
    return b.getImage()

def makeVyrobaSticker(e: Vyroba, t: Team, stype: StickerType) -> Image:
    assert stype == StickerType.regular

    b = getDefaultStickerBuilder()
    makeStickerHeader(e, t, b)

    featureText = ", ".join([f.name for f in e.requiredFeatures])
    b.addBulletLine("Vyžaduje: ", featureText, FONT_NORMAL, bulletFont=FONT_BOLD)
    b.skip(5)
    b.addText("Vstupy:", FONT_BOLD)
    with b.withOffset(10):
        for r, a in e.cost.items():
            b.addBulletLine("• ", f"{a}× {r.name}", FONT_NORMAL)
    b.addBulletLine("Výstup: ", f"{e.reward[1]}× {e.reward[0].name}", FONT_NORMAL,
        bulletFont=FONT_BOLD)

    makeStickerFooter(e, b)
    return b.getImage()

def makeVoucherSticker(effect: DbDelayedEffect) -> Image:
    b = getDefaultStickerBuilder()

    b.hline(3, 0)
    b.skip(100)
    b.hline(3, 0)
    b.skip(5)
    qr = makeQrCode(f"vou-{effect.slug.upper()}", pixelSize=3, borderQrPx=4)

    b.img.paste(qr, (b.offset + b.margin - 12, b.position))
    qrBottom = b.position + qr.height
    b.skip(12)
    with b.withOffset(qr.width):
        b.addText(f"Směnka pro {effect.team.name}", FONT_BOLD)
        b.addText(f"Kód: {effect.slug.upper()}", FONT_BOLD)
    b.position = max(b.position, qrBottom) + 10
    b.addText(f"Nabývá efektu v {effect.round}–{math.floor(effect.target // 60)}:{effect.target % 60}", FONT_BOLD)
    b.hline(1, 0)
    b.skip(5)
    b.skip(40)
    b.hline(3, 0)
    return b.getImage()

STICKER_CACHE = FileCache(settings.CACHE / "stickers", ".png")

def getStickerFile(stickerModel: DbSticker) -> Path:
    _, entities = DbEntities.objects.get_revision(stickerModel.entityRevision)
    def render(path):
        s = makeSticker(entities[stickerModel.entityId], stickerModel.team, stickerModel.type)
        s.save(path)
    return STICKER_CACHE.path(stickerModel.ident, render)

if __name__ == "__main__":
    from game.tests.actions.common import TEST_ENTITIES

    vyroba = makeSticker(TEST_ENTITIES["vyr-drevo1Pro"], StickerType.regular)
    # vyroba.show()
    tech = makeSticker(TEST_ENTITIES["tec-start"], StickerType.regular)
    tech.show()
    tech.save("test.png")
