from django.shortcuts import render

# Create your views here.

def renta_view(request):
    return render(request, print("Hola desde la vista de renta"))