import contextlib
from typing import List
from PIL import Image, ImageDraw, ImageFont, ImageOps
import qrcode

ROBOTO_NORMAL = ImageFont.truetype("data/fonts/Roboto-Regular.ttf", 18)
ROBOTO_BOLD = ImageFont.truetype("data/fonts/Roboto-Bold.ttf", 25)


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

    def addBulletLine(self, bullet, text, font) -> int: # bullet offset
        bulletBox = self.drawInt.textbbox(
            xy=(self.margin + self.offset, self.position),
            text=bullet,
            font=font,
        )
        # Draw bullet:
        self.drawInt.text(
            xy=(self.margin + self.offset, self.position),
            text=bullet,
            font=font,
            anchor="la",
            align="left",
            fill=(0,0,0))
        with self.withOffset(bulletBox[2]):
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

    def hline(self, width: int=4, margin: int=10) -> None:
        self.drawInt.line([(self.margin + margin, self.position),
                           (self.img.width - self.margin - margin, self.position)],
                           fill=(0, 0, 0), width=width, joint="curve")
        self.position += width

    def getImage(self) -> Image:
        bbox = ImageOps.invert(self.img).getbbox()
        return self.img.crop((0, 0, self.img.width, bbox[3] + self.margin))


if __name__ == "__main__":
    b = StickerBuilder(333, 15)
    b.skip(10)
    b.hline()
    b.skip(5)
    qr = makeQrCode("team-zeleni vyr-bobule", pixelSize=3)

    b.img.paste(qr, (b.offset + b.margin - 12, b.position))
    qrBottom = b.position + qr.height
    b.skip(12)
    with b.withOffset(qr.width):
        b.addText("Tady je nějaký dlouhý název výroby", ROBOTO_BOLD)
    b.position = max(b.position, qrBottom) + 10

    for i in range(3):
        offset = b.addBulletLine("•", "Same as arc, but also draws straight lines between the end points and the center of the bounding box.", ROBOTO_NORMAL)
        with b.withOffset(offset):
            for i in range(3):
                b.addBulletLine("–", "Another, rather long, long, long, long text", ROBOTO_NORMAL)
    b.skip(10)
    b.hline()

    b.getImage().show()
    b.getImage().save("test.png")
