from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.forms import formset_factory

from game.models.messageBoard import Message, MessageStatus
from game.models.users import Team

from game.forms.messageBoard import MessageForm, TeamVisibilityForm

def messageVisibilityForm(message=None, data=None):
    teams = Team.objects.all()
    TeamVisibilityFormset = formset_factory(TeamVisibilityForm, extra=len(teams))
    form = TeamVisibilityFormset(data) if data else TeamVisibilityFormset()
    for i, team in enumerate(teams):
        if not data: # If we override the initial when there are data, they disappear
            form[i].fields["team"].initial = team.id
        form[i].fields["visible"].label = team.name
        if message:
            form[i].fields["visible"].initial = message.messagestatus_set.get(team=team.id).visible
    return form

class IndexView(View):
    @method_decorator(login_required)
    def get(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        boardMessages = Message.objects.all() \
            .prefetch_related("messagestatus_set").order_by('-appearDateTime')
        return render(request, "game/messageBoardIndex.html", {
            "request": request,
            "boardMessages": boardMessages,
            "messages": messages.get_messages(request)
        })

class NewMessageView(View):
    @method_decorator(login_required)
    def get(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        messageForm = MessageForm()
        visibilityForm = messageVisibilityForm()
        return render(request, "game/messageBoardMessage.html", {
            "request": request,
            "messageForm": messageForm,
            "visibilityForm": visibilityForm,
            "messages": messages.get_messages(request)
        })

    @method_decorator(login_required)
    def post(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        messageForm = MessageForm(request.POST)
        visibilityForm = messageVisibilityForm(data=request.POST)
        if messageForm.is_valid() and visibilityForm.is_valid():
            message = Message.objects.create(
                content = messageForm.cleaned_data["content"],
                appearDateTime = messageForm.cleaned_data["appearDateTime"],
                author = request.user)
            for visibility in visibilityForm.cleaned_data:
                status = MessageStatus.objects.create(
                    team = Team.objects.get(pk=visibility["team"]),
                    message = message,
                    visible = visibility["visible"]
                )
            messages.success(request, "Zpráva vytvořena")
            return redirect("messageBoardIndex")
        return render(request, "game/messageBoardMessage.html", {
            "request": request,
            "messageForm": messageForm,
            "visibilityForm": visibilityForm,
            "messages": messages.get_messages(request)
        })

class EditMessageView(View):
    @method_decorator(login_required)
    def get(self, request, messageId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        message = get_object_or_404(Message, pk=messageId)
        messageForm = MessageForm(message=message)
        visibilityForm = messageVisibilityForm(message)
        return render(request, "game/messageBoardMessage.html", {
            "edit": True,
            "request": request,
            "messageForm": messageForm,
            "visibilityForm": visibilityForm,
            "messages": messages.get_messages(request)
        })

    @method_decorator(login_required)
    def post(self, request, messageId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        messageForm = MessageForm(request.POST)
        visibilityForm = messageVisibilityForm(data=request.POST)
        if messageForm.is_valid() and visibilityForm.is_valid():
            message = get_object_or_404(Message, pk=messageId)
            message.content = messageForm.cleaned_data["content"]
            message.appearDateTime = messageForm.cleaned_data["appearDateTime"]
            message.author = request.user

            for visibility in visibilityForm.cleaned_data:
                status = MessageStatus.objects.get(message=message.id, team=visibility["team"])
                status.visible = visibility["visible"]
                status.save()
            message.save()
            messages.success(request, "Zpráva upravena")
            return redirect("messageBoardIndex")
        return render(request, "game/messageBoardMessage.html", {
            "edit": True,
            "request": request,
            "messageForm": messageForm,
            "visibilityForm": visibilityForm,
            "messages": messages.get_messages(request)
        })

class DeleteMessageView(View):
    @method_decorator(login_required)
    def get(self, request, messageId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        message = get_object_or_404(Message, pk=messageId)
        return render(request, "game/messageBoardDelete.html", {
            "request": request,
            "message": message,
            "messages": messages.get_messages(request)
        })

    @method_decorator(login_required)
    def post(self, request, messageId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        message = get_object_or_404(Message, pk=messageId)
        message.delete()
        messages.success(request, "Zpráva smazána")
        return redirect("messageBoardIndex")

class DismissMessageView(View):
    @method_decorator(login_required)
    def get(self, request, messageId):
        next = request.GET.get('next', '/')
        if not request.user.isPlayer():
            messages.warning(request, "Organizátor nemůže účastníkům skrývat zprávy")
            return redirect(next)
        try:
            status = MessageStatus.objects.get(message=messageId, team=request.user.team().pk)
        except MessageStatus.DoesNotExist:
            messages.error(request, "Organizátor nemůže účastníkům skrývat zprávy")
            return redirect(next)
        status.read = True
        status.save()
        messages.success(request, "Zpráva označena jako přečtená")
        return redirect(next)