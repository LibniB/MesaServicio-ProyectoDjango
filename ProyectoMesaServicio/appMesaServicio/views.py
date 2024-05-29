from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render, redirect 
from django.contrib.auth import authenticate
from django.contrib import auth
from appMesaServicio.models import *
from random import *
from django.db import Error,transaction
#PARA CORREO
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
import threading
from smtplib import SMTPException

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
                      "oficinasAmbientes":oficinaAmbientes}
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
            
            fecha = datetime.now()
            year = fecha.year
            
            consecutivoCaso=Solicitud.objects.filter(fechaHoraCreacion__year=year).count()
            consecutivoCaso = str(consecutivoCaso).rjust(5,'0')
            codigoCaso=f"REQ-{year}-{consecutivoCaso}"
            userCaso = User.objects.filter(groups__name__in=['Administrador']).first()
            estado ="Solicitada"
            caso = Caso(casSolicitud=solicitud,
                        casCodigo=codigoCaso,
                        casUsuario=userCaso,
                        casEstado=estado)
            caso.save()
            #enviar correo 
            asunto='Registro solicitud - Mesa de Servicio'
            mensajeCorreo=f'Cordial saludo, <b>{user.first_name} {user.last_name}</b>, nos permitimos \
                informarle que su solicitud fue registrada en nuestro sistema con el número de caso \
                <b>{codigoCaso}</b>. <br><br> Su caso será gestionado en el menor tiempo posible, \
                según los acuerdos de solución establecidos para la Mesa de Servicios del CTPI-CAUCA.\
                <br><br>Lo invitamos a ingresar a nuestro sistema en la siguiente url:\
                http://mesadeservicioctpicauca.sena.edu.co.'
            thread= threading.Thread(
                target=enviarCorreo, args=(asunto, mensajeCorreo,[user.email]))
            thread.start()
            mensaje="Se ha registrado su solicitud de manera exitosa"
    except Error as error:
        transaction.rollback()
        mensaje=f"error"
        
    oficinaAmbientes= OficinaAmbiente.objects.all()
    retorno = {"mensaje":mensaje,"oficinasAmbientes":oficinaAmbientes}
    return render(request,"empleado/solicitud.html",retorno)
           
            

def enviarCorreo(asunto=None,mensaje=None,destinatario=None,archivo=None):
    remitente = settings.EMAIL_HOST_USER
    template = get_template('enviarCorreo.html')
    contenido = template.render({
        'mensaje':mensaje,
    })
    try:
        correo = EmailMultiAlternatives(
            asunto,mensaje,remitente,destinatario)
        correo.attach_alternative(contenido,'text/html')
        
        if archivo != None:
            correo.attach_file(archivo)
        correo.send(fail_silently=True)
        print("enviado")
    except SMTPException as error:
        print(error)
        

def listarCasos(request):
        try:
            mensaje=""
            listaCasos= Caso.objects.all()
            tecnicos = User.objects.filter(groups__name__in=['Tecnico'])
            
        except Error as error:
            mensaje= str(error)
        retorno = {"listaCasos":listaCasos, 
                "tecnicos":tecnicos, 
                "mensaje":mensaje}
        return render(request, "administrador/listarCasos.html",retorno)
    
def listarEmpleadosTecnicos(request):
    try:
        mensaje=""
        tecnicos = User.objects.filter(groups__name__in=['Tecnico'])
    except Error as error:
        mensaje= str(error)
    retorno={"tecnico":tecnicos, "mensaje":mensaje}
    
    return JsonResponse(retorno)


def asignarTecnicoCaso(request):
    if request.user.is_authenticated:
        try:
            idTecnico= int(request.POST['cbTecnico'])
            userTecnico = User.objects.get(pk=idTecnico)
            idCaso= int(request.POST['idCaso'])
            caso = Caso.objects.get(pk=idCaso)
            caso.casUsuario = userTecnico
            caso.casEstado = "En Proceso"
            caso.save()
            #enviar correo al tecnico
            asunto='Asignacion caso - mesa de servicio'
            mensajeCorreo=f'Cordial saludo, <b>{userTecnico.first_name} {userTecnico.last_name}</b>, nos permitimos \
                informarle que se le ha asignado un caso para dar solucion. Codigo de caso: \
                <b>{caso.casCodigo}</b>. <br><br> Se solicita se atienda de manera oportuna \
                según los acuerdos de solución establecidos para la Mesa de Servicios del CTPI-CAUCA.\
                <br><br>Lo invitamos a ingresar al sistema para gestionar sus casos asignados en la siguiente url:\
                http://mesadeservicioctpicauca.sena.edu.co.'
            thread= threading.Thread(
                target=enviarCorreo, args=(asunto, mensajeCorreo,[userTecnico.email]))
            thread.start()
            mensaje="Caso asignado"
        except Error as error:
            mensaje = str(error)
        return redirect('/listarCasosParaAsignar/')
    else:
        mensaje = "Debe iniciar sesion"
    return render(request,"frmIniciarSesion.html",{"mensaje":mensaje})

def salir(request):
    auth.logout(request)
    return render(request,"frmIniciarSesion.html",
                  {"mensaje":"Ha cerrado la sesion"})
    
    
    