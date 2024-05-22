from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib import auth
from appMesaServicio.models import *
from random import *
from django.db import Error,transaction
# Create your views here.

def inicio(request):
    return render(request, "frmIniciarSesion.html")


def inicioEmpleado (request):
    if request.user.is_authenticated:
        datosSesion = {"user":request.user,
                      "rol": request.user.groups.get().name}
        return render(request,"empleado/inicio.html",datosSesion)
    else:
        mensaje = "Debe iniciar sesion"
    return render(request,"frmIniciarSesion.html",{"mensaje":mensaje})


def inicioAdministrador (request):
    if request.user.is_authenticated:
        datosSesion = {"user":request.user,
                      "rol": request.user.groups.get().name}
        return render(request,"administrador/inicio.html",datosSesion)
    else:
        mensaje = "Debe iniciar sesion"
    return render(request,"frmIniciarSesion.html",{"mensaje":mensaje})


def inicioTecnico (request):
    if request.user.is_authenticated:
        datosSesion = {"user":request.user,
                      "rol": request.user.groups.get().name}
        return render(request,"tecnico/inicio.html",datosSesion)
    else:
        mensaje = "Debe iniciar sesion"
    return render(request,"frmIniciarSesion.html",{"mensaje":mensaje})


def login (request):
    username = request.POST["txtUser"]
    password = request.POST["txtPassword"]
    user = authenticate(username=username, password=password)
    
    if user is not None:
        auth.login(request, user)
        if user.groups.filter(name='Administrador').exists():
            return redirect('/inicioAdministrador')
        elif user.groups.filter(name='Tecnico').exists():
            return redirect('/inicioTecnico')
        else:
            return redirect('/inicioEmpleado')
    else:
        mensaje="Usuario o Contraseña incorrectas"
        return render(request,"frmIniciarSesion.html",{"mensaje":mensaje})

def vistaSolicitud (request):
    if request.user.is_authenticated:
        oficinaAmbientes = OficinaAmbiente.objects.all()
        datosSesion = {"user":request.user,
                      "rol": request.user.groups.get().name,
                      "oficinaAmbientes":oficinaAmbientes}
        return render(request,'empleado/solicitud.html',datosSesion)
    else:
        mensaje = "Debe iniciar sesion"
        return render(request,"frmIniciarSesion.html",{"mensaje":mensaje})
    
def registroSolicitud (request):
    try:
        with transaction.atomic():
            user = request.user 
            descripcion = request.POST['txtDescripcion'] 
            idOficinaAmbiente = int(request.POST['cbOficinaAmbiente'])
            oficinaAmbiente = OficinaAmbiente.objects.get(pk=idOficinaAmbiente)
            solicitud = Solicitud(
                solUsuario = user,
                solDescripcion = descripcion,
                solOficinaAmbiente = oficinaAmbiente
            )
            solicitud.save()
            
            consecutivoCaso = randint(1, 10000)
            codigoCaso="REQ" + str(consecutivoCaso).rjust(5,'0')
            userCaso = User.objects.filter(groups__name__in=['Administrador'])
            estado="Solicitada"
            caso = Caso(casSolicitud=solicitud,
                        casCodigo=codigoCaso,
                        casUsuario=userCaso,
                        casEstado=estado)
            caso.save()
            
    except Error as error:
        transaction.rollback()
        mensaje = f"{error}"
        
        

def salir(request):
    auth.logout(request)
    return render(request,"frmIniciarSesion.html",
                  {"mensaje":"Ha cerrado la sesion"})