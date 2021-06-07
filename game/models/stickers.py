from django.db import models
from django_enumfield import enum
from game.data.entity import EntityModel
from PIL import Image, ImageDraw
import io
import os
from pathlib import Path

class FileCache:
    def __init__(self, cacheDirectory, suffix):
        self.cacheDirectory = cacheDirectory
        Path(cacheDirectory).mkdir(exist_ok=True)
        self.suffix = suffix

    def get(self, ident, renderer):
        """
        Given an object ident (something convertible to string) and renderer
        (function that can render the object to bytes), return the object either
        from cache or by rendering it.
        """
        cacheFile = os.path.join(self.cacheDirectory, f"{ident}.{self.suffix}")
        try:
            with open(cacheFile, "rb") as f:
                return f.read()
        except FileNotFoundError:
            # File is not in cache
            content = renderer()
            with open(cacheFile, "wb") as f:
                f.write(content)
            return content

STICKER_CACHE = FileCache("./_stickers", "png")

class StickerType(enum.Enum):
    REGULAR = 0
    PUBLIC = 1
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

    def shortDescription(self):
        """
        Return a pretty short string description of the sticker
        """
        return f"Sticker \nfor team {self.team.id} \nof {self.entity.id}"

    def getImage(self):
        """
        Return sticker image as PNG file in bytes
        """
        return STICKER_CACHE.get(f"sticker_{self.id:04d}", lambda: self.render())

    def render(self):
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
