if __name__ == "__main__":
    import django

    django.setup()

import contextlib
import os
from collections.abc import Generator
from decimal import Decimal
from pathlib import Path
from typing import Mapping, Optional, Tuple

import boolean
import qrcode
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont, ImageOps

from backend.settings import ICON_PATH
from core.models.team import Team
from game.entities import (
    RESOURCE_WORK,
    Building,
    BuildingUpgrade,
    Entities,
    Entity,
    Resource,
    TeamAttribute,
    Tech,
    Vyroba,
)
from game.models import DbEntities, DbSticker, StickerType
from game.util import FileCache, requirements_str

FONT_NORMAL = ImageFont.truetype(
    os.path.join(settings.DATA_PATH, "fonts", "Roboto-Regular.ttf"), 20
)
FONT_BOLD = ImageFont.truetype(
    os.path.join(settings.DATA_PATH, "fonts", "Roboto-Bold.ttf"), 20
)
FONT_HEADER = ImageFont.truetype(
    os.path.join(settings.DATA_PATH, "fonts", "Roboto-Bold.ttf"), 30
)


def makeQrCode(content: str, pixelSize: int = 3, borderQrPx: int = 4) -> Image.Image:
    qr = qrcode.QRCode(
        error_correction=qrcode.ERROR_CORRECT_H,
        box_size=pixelSize,
        border=borderQrPx,
    )
    qr.add_data(content)
    qr.make(fit=True)

    return qr.make_image(fill_color="black", back_color="white").get_image()


class StickerBuilder:
    def __init__(self, width, xMargin: int = 5, yMargin: int = 20):
        self.img = Image.new("RGB", (width, 10 * width), color=(255, 255, 255))
        self.xMargin = xMargin
        self.yMargin = yMargin
        self.offset = 0
        self.yPosition = self.yMargin
        self.drawInt = ImageDraw.Draw(self.img)

    def _breakIntoLines(self, text: str, font: ImageFont.FreeTypeFont) -> list[str]:
        # Let's do it in a stupid way. TBA optimize
        words = text.split(" ")
        lines = []
        last = 0
        for i in range(1, len(words) + 1):
            l = " ".join(words[last:i])
            box = self.drawInt.textbbox(
                xy=(self.xMargin + self.offset, 0), text=l, font=font
            )
            if box[2] > self.img.width - self.xMargin:
                # If we cannot fit a single word on a line, just overflow it
                if last == i - 1:
                    i += 1
                lines.append(" ".join(words[last : i - 1]))
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
                fill=(0, 0, 0),
            )
            self.yPosition = box[3]

    def addBulletLine(
        self, bullet, text, font, bulletFont=None
    ) -> int:  # bullet offset
        if bulletFont is None:
            bulletFont = font
        bulletBox = self.drawInt.textbbox(
            xy=(self.xMargin + self.offset, self.yPosition),
            text=bullet,
            font=bulletFont,
        )
        # Draw bullet:
        self.drawInt.text(
            xy=(self.xMargin + self.offset, self.yPosition),
            text=bullet,
            font=bulletFont,
            anchor="la",
            align="left",
            fill=(0, 0, 0),
        )
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

    def hline(self, width: int = 4, margin: int = 0) -> None:
        self.drawInt.line(
            [
                (self.xMargin + margin, self.yPosition),
                (self.img.width - self.xMargin - margin, self.yPosition),
            ],
            fill=(0, 0, 0),
            width=width,
            joint="curve",
        )
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

    def getImage(self, height: Optional[int] = None) -> Image.Image:
        if height is None:
            bbox = ImageOps.invert(self.img).getbbox()
            assert bbox is not None, "Image is empty"
            height = bbox[3] + self.yMargin
        return self.img.crop((0, 0, self.img.width, height))

    def getTextSize(self, text, font):
        return self.drawInt.textbbox(xy=(0, 0), text=text, font=font)


def makeSticker(
    e: Entity, t: Team, stype: StickerType, *, entities: Entities
) -> Image.Image:
    if isinstance(e, Tech):
        return makeTechSticker(e, t, stype, entities=entities)
    if isinstance(e, Vyroba):
        return makeVyrobaSticker(e, t, stype, entities=entities)
    if isinstance(e, Building):
        return makeBuildingSticker(e, t, stype, entities=entities)
    if isinstance(e, BuildingUpgrade):
        return makeBuildingUpgradeSticker(e, t, stype, entities=entities)
    if isinstance(e, TeamAttribute):
        return makeTeamAttributeSticker(e, t, stype, entities=entities)
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


def makeStickerHeader(
    e: Entity, t: Optional[Team], builder: StickerBuilder, first: bool = False
) -> None:
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


def sortedCost(cost: Mapping[Resource, Decimal]) -> list[Tuple[Resource, Decimal]]:
    def keyFn(item: Tuple[Resource, Decimal]):
        r, a = item
        if r.id == RESOURCE_WORK:
            index = 0
        elif not r.tradable:
            index = 1
        elif r.isTradableProduction:
            index = 2
        else:
            index = 3
        return (index, r.name, r.id)

    return sorted(((r, a) for r, a in cost.items() if a != 0), key=keyFn)


def resourceName(resource):
    n = resource.name.replace(" ", " ")
    if isinstance(resource, Resource) and resource.isTradableProduction:
        return underline(n)
    return n


def print_requirements(requirements: boolean.Expression, entities: Entities) -> str:
    return requirements_str(
        requirements, lambda id: resourceName(entities[id]) if id in entities else id
    )


def makeTechSticker(
    e: Tech, team: Team, stype: StickerType, *, entities: Entities
) -> Image.Image:
    b = getDefaultStickerBuilder()
    makeStickerHeader(e, team, b, first=stype == StickerType.techFirst)

    if stype == StickerType.techSmall:
        return b.getImage()

    if len(e.flavor) > 0:
        b.addText(e.flavor, FONT_NORMAL)

    uVyrobas = e.unlocksVyrobas
    if len(uVyrobas) > 0:
        vText = ", ".join([v.name for v in uVyrobas])
        b.addText(f"Umožňuje vyrábět: ", FONT_BOLD)
        b.addText(vText, FONT_NORMAL)
        b.skip(10)

    uBuildings = e.unlocksBuildings
    if len(uBuildings) > 0:
        bText = ", ".join([v.name for v in uBuildings])
        b.addText(f"Umožňuje stavět: ", FONT_BOLD)
        b.addText(bText, FONT_NORMAL)
        b.skip(10)

    uAttributes = e.unlocksTeamAttributes
    if len(uAttributes) > 0:
        bText = ", ".join([v.name for v in uAttributes])
        b.addText(f"Umožňuje získat vlastnosti: ", FONT_BOLD)
        b.addText(bText, FONT_NORMAL)
        b.skip(10)

    bulletWidth = b.getTextSize(text="• ", font=FONT_NORMAL)[2]

    uTechs = sorted(e.unlocksTechs, key=lambda x: x.name)
    if len(uTechs) > 0:
        b.skip(5)
        b.addText("Odemyká směry bádání:", FONT_BOLD)
        with b.withOffset(10):
            for t in uTechs:
                costText = ", ".join(
                    [f"{a}× {resourceName(r)}" for r, a in sortedCost(t.cost)]
                )
                b.addText(f"• {t.name}: ", FONT_BOLD)
                with b.withOffset(b.offset + bulletWidth):
                    if t.requirements is not None:
                        b.addText(
                            f"Vyžaduje: {print_requirements(t.requirements, entities)}",
                            FONT_NORMAL,
                        )
                    b.addText(f"Kostka: {t.points}", FONT_NORMAL)
                    b.addText(f"Cena: {costText}", FONT_NORMAL)

    if e.icon is not None:
        icon = os.path.splitext(e.icon)[0] + "-lg.png"
        b.skip(10)
        try:
            b.addIcon(icon)
        except Exception:
            pass

    makeStickerFooter(e, b)
    return b.getImage(mm2Pt(95))


def makeBuildingSticker(
    e: Building, t: Team, stype: StickerType, *, entities: Entities
) -> Image.Image:
    assert stype == StickerType.regular

    b = getDefaultStickerBuilder()
    makeStickerHeader(e, t, b)

    if e.requirements is not None:
        b.addBulletLine(
            "Vyžaduje: ",
            print_requirements(e.requirements, entities),
            FONT_NORMAL,
            FONT_BOLD,
        )
    featureText = ", ".join(f.name for f in e.requiredTileFeatures)
    if len(featureText) > 0:
        b.addBulletLine("Vyžaduje na poli: ", featureText, FONT_NORMAL, FONT_BOLD)
    b.skip(5)
    b.addBulletLine("Kostka: ", str(e.points), FONT_NORMAL, FONT_BOLD)
    b.addText("Cena:", FONT_BOLD)
    with b.withOffset(10):
        for r, a in sortedCost(e.cost):
            b.addBulletLine("• ", f"{a}× {resourceName(r)}", FONT_NORMAL)

    if len(e.upgrades) > 0:
        b.skip(10)
        upgradeText = ", ".join(u.name for u in e.upgrades)
        b.addBulletLine("Vylepšení: ", upgradeText, FONT_NORMAL, FONT_BOLD)

    if e.icon is not None:
        icon = os.path.splitext(e.icon)[0] + "-lg.png"
        b.skip(10)
        try:
            b.addIcon(icon)
        except Exception:
            pass

    makeStickerFooter(e, b)

    return b.getImage()


def makeBuildingUpgradeSticker(
    e: BuildingUpgrade, t: Team, stype: StickerType, *, entities: Entities
) -> Image.Image:
    assert stype == StickerType.regular

    b = getDefaultStickerBuilder()
    makeStickerHeader(e, t, b)

    b.addBulletLine("Budova: ", e.building.name, FONT_NORMAL, FONT_BOLD)
    if e.requirements is not None:
        b.addBulletLine(
            "Vyžaduje: ",
            print_requirements(e.requirements, entities),
            FONT_NORMAL,
            FONT_BOLD,
        )
    b.skip(5)
    b.addBulletLine("Kostka: ", str(e.points), FONT_NORMAL, FONT_BOLD)
    b.addText("Cena:", FONT_BOLD)
    with b.withOffset(10):
        for r, a in sortedCost(e.cost):
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


def makeTeamAttributeSticker(
    e: TeamAttribute, t: Team, stype: StickerType, *, entities: Entities
) -> Image.Image:
    assert stype == StickerType.regular

    b = getDefaultStickerBuilder()
    makeStickerHeader(e, t, b)

    if e.requirements is not None:
        b.addBulletLine(
            "Vyžaduje: ",
            print_requirements(e.requirements, entities),
            FONT_NORMAL,
            FONT_BOLD,
        )
    b.skip(5)
    b.addBulletLine("Kostka: ", str(e.points), FONT_NORMAL, FONT_BOLD)
    b.addText("Cena:", FONT_BOLD)
    with b.withOffset(10):
        for r, a in sortedCost(e.cost):
            b.addBulletLine("• ", f"{a}× {resourceName(r)}", FONT_NORMAL)

    if e.icon is not None:
        icon = os.path.splitext(e.icon)[0] + "-lg.png"
        b.skip(10)
        try:
            b.addIcon(icon)
        except Exception:
            pass

    makeStickerFooter(e, b)

    return b.getImage()


def makeVyrobaSticker(
    e: Vyroba, t: Team, stype: StickerType, *, entities: Entities
) -> Image.Image:
    assert stype == StickerType.regular

    b = getDefaultStickerBuilder()
    makeStickerHeader(e, t, b)

    if len(e.flavor) > 0:
        b.addText(e.flavor, FONT_NORMAL)

    if e.requirements is not None:
        b.addBulletLine(
            "Vyžaduje: ",
            print_requirements(e.requirements, entities),
            FONT_NORMAL,
            FONT_BOLD,
        )
    featureText = ", ".join(f.name for f in e.requiredTileFeatures)
    if len(featureText) > 0:
        b.addBulletLine(
            "Vyžaduje na poli: ", featureText, FONT_NORMAL, bulletFont=FONT_BOLD
        )
    b.skip(5)
    b.addBulletLine("Kostka: ", f"{e.points}", FONT_NORMAL, FONT_BOLD)
    b.addText("Vstupy:", FONT_BOLD)
    with b.withOffset(10):
        for r, a in sortedCost(e.cost):
            b.addBulletLine("• ", f"{a}× {resourceName(r)}", FONT_NORMAL)

    b.addBulletLine(
        "Výstup: ",
        f"{e.reward[1]}× {resourceName(e.reward[0])}",
        FONT_NORMAL,
        bulletFont=FONT_BOLD,
    )
    if len(e.otherRewards) > 0:
        b.addText("Další výstupy:", FONT_BOLD)
        with b.withOffset(10):
            for r, a in e.otherRewards:
                if a == 0:
                    continue
                b.addBulletLine("• ", f"{a}× {resourceName(r)}", FONT_NORMAL)

    icon = e.reward[0].icon
    if icon is not None:
        icon = os.path.splitext(icon)[0] + "-md.png"
        b.skip(10)
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
        s = makeSticker(
            entities[stickerModel.entityId],
            stickerModel.team,
            stickerModel.type,
            entities=entities,
        )
        s.save(path)

    return STICKER_CACHE.path(stickerModel.ident, render)


if __name__ == "__main__":
    from game.tests.actions.common import TEST_ENTITIES

    team_zeleni = Team.objects.model(id="tea-zeleni", name="Zelení", color="green")

    vyroba = makeSticker(
        TEST_ENTITIES["vyr-drevo1Pro"],
        team_zeleni,
        StickerType.regular,
        entities=TEST_ENTITIES,
    )
    # vyroba.show()
    tech = makeSticker(
        TEST_ENTITIES["tec-start"],
        team_zeleni,
        StickerType.regular,
        entities=TEST_ENTITIES,
    )
    tech.show()
    tech.save("test.png")
