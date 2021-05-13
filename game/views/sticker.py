from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
import io

from game.models.stickers import Sticker

class StickerView(View):
    @method_decorator(login_required)
    def get(self, request, stickerId):
        sticker = get_object_or_404(Sticker, id=stickerId)
        user = request.user
        if not user.isOrg() and user.team().id != sticker.team:
            raise PermissionDenied()
        buffer = io.BytesIO(sticker.getImage())
        return FileResponse(buffer, filename=f"sticker_{stickerId}.png")

