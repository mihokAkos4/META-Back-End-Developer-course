from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.

def home (request):
    content = "<h1> Welcome to Little Lemon! </h1>"
    return HttpResponse(content)