from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def sign_in(request):
  if request.method == 'GET':
    return render(request, 'login/login.html')
  else:
    user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
    if user is None:
      return render(request, 'login/login.html',{
        'error': 'Usuario o contraseña inválidos'
      })
    else:
      login(request, user)
      return redirect('pomi:dashboard')