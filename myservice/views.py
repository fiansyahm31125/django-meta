from django.shortcuts import render,redirect
from django.http import HttpResponse
from .models import Service

# Create your views here.
def index(request):
    if request.method!='POST':
        services=Service.objects.all()
        return render(request,'service.html',{'services':services})
    else:
        try:
            name=request.POST.get('name')
            type=request.POST.get('type')
            newdata=Service.objects.create(name=name,type=type)
            return redirect('service_index')
        except:
            pass
