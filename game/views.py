from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request, 'game/dashboard.html')

def demo(request):
    return render(request, 'demo.html')
