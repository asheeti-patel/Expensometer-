from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # just save, don't log in
            return redirect('login')  # go to login page
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def home_view(request):
    return render(request, 'home.html')
