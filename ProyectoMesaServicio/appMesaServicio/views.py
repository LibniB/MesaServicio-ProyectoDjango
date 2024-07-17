from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render, redirect 
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_protect, csrf_exempt
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
#para contraseña
import string
import random
#importar modelo 
from django.contrib.auth.models import Group
# api
from rest_framework import generics
from appMesaServicio.serializers import OficinaAmbienteSerializer

# graficos estadisticos
from django.db.models import Count
import matplotlib.pyplot as plt
import os
from django.db.models.functions import ExtractMonth
import calendar


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

@csrf_exempt
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

def listarCasosAsignadosTecnico(request):
    if request.user.is_authenticated:
        try:
            mensaje=""
            listaCasos= Caso.objects.filter(casEstado='En Proceso',casUsuario=request.user)
            listarTipoProcedimiento = TipoProcedimiento.objects.all().values()
        except Error as error:
            mensaje= str(error)
        retorno ={"mensaje":mensaje,"listaCasos":listaCasos,
                  "listaTipoSolucion":tipoSolucion,
                  "listarTipoProcedimiento":listarTipoProcedimiento}
        
        return render (request,"tecnico/listarCasosAsignados.html",retorno)
    else:
        mensaje = "Debe iniciar sesion"
    return render(request,"frmIniciarSesion.html",{"mensaje":mensaje})

def solucionarCaso(request):
    if request.user.is_authenticated:
        try:
            if transaction.atomic():
                procedimiento = request.POST['txtProcedimiento']
                tipoProc = request.POST['cbTipoProcedimiento']
                tipoProcedimiento = TipoProcedimiento.objects.get(pk=tipoProc)
                tipoSolucion = request.POST['cbTipoSolucion']
                idCaso =int(request.POST['idCaso'])
                caso = Caso.objects.get(pk=idCaso)
                solucionCaso= SolucionCaso(solCaso=caso,
                                        solProcedimiento=procedimiento,
                                        solTipoSolucion=tipoSolucion)
                
                solucionCaso.save()
                #actulizar estado de caso dependiendo dle tipo de solucion
                if(tipoSolucion == "Definitiva"):
                    caso.casEstado="Finalizada"
                    caso.save()
                    
                #crear el objeto solcuoon tipo procedimiento
                solucionCasoTipoProcedimiento=SolucionCasoTipoProcedimientos(solSolucionCaso=solucionCaso,
                                                                            solTipoProcedimiento=tipoProcedimiento)
                solucionCasoTipoProcedimiento.save()
                
                #enviar correo al empleado que realizó la solicitud
                solicitud= caso.casSolicitud
                userEmpleado = solicitud.solUsuario
                
                print("Dirección de correo electrónico del usuario:", userEmpleado.email)
                
                asunto='Solucion caso - CTPI CAUCA'
                mensajeCorreo= f"""Cordial saludo, <b>{userEmpleado.first_name} {userEmpleado.last_name}</b>, nos permitimos informarle que se ha dado solucion de tipo {tipoSolucion} al caso identificado con codigo: 
                <b>{caso.casCodigo}</b>. <br><br> Lo invitamos a revisar el equipo y verificar la solucion.<br><br>
                Para consultar en detalle la solucion,ingresar al sistema para gestionar sus casos asignados en la siguiente url:<br>
                http://mesadeservicioctpicauca.sena.edu.co."""
                thread= threading.Thread(
                target=enviarCorreo, args=(asunto, mensajeCorreo,[userEmpleado.email]))
                thread.start()
        except Error as error:
            transaction.rollback()
            mensaje= str(error)
        retorno = {"mensaje":mensaje}
        return redirect("/listarCasosAsignados/")
    else:
        mensaje = "Debe iniciar sesion"
        return render(request,"frmIniciarSesion.html",{"mensaje":mensaje})


def listarSolicitudes(request):
    if request.user.is_authenticated:
        try:
            mensaje=""
            caso = Caso.objects.all()
            
        except Error as error:
            mensaje= str(error)
        retorno = {"mensaje":mensaje,"caso":caso}
        return render(request,"empleado/listarSolicitudes.html",retorno)
    else:
        mensaje = "Debe iniciar sesion"
    return render(request,"frmIniciarSesion.html",{"mensaje":mensaje})



def vistaGestionarUsuarios(request):
    if request.user.is_authenticated:
        usuarios = User.objects.all()
        retorno = {"usuarios": usuarios, "user": request.user,
                   "rol": request.user.groups.get().name}
        return render(request, "administrador/vistaGestionarUsuario.html", retorno)
    else:
        mensaje = "Debe iniciar sesión"
        return render(request, "frmIniciarSesion.html", {"mensaje": mensaje})


def vistaRegistrarUsuario(request):
    if request.user.is_authenticated:
        roles = Group.objects.all()
        retorno = {"roles": roles, "user": request.user, 'tipoUsuario': tipoUsuario,
                   "rol": request.user.groups.get().name}
        return render(request, "administrador/frmRegistrarUsuario.html", retorno)
    else:
        mensaje = "Debe iniciar sesión"
        return render(request, "frmIniciarSesion.html", {"mensaje": mensaje})

def registrarUsuario(request):
    if request.user.is_authenticated:
        try:
            nombres = request.POST['txtNombres']
            apellidos = request.POST['txtApellidos']
            correo = request.POST['txtCorreo']
            tipo = request.POST['cbTipo']
            foto = request.FILES.get("fileFoto")
            idRol = int(request.POST['cbRol'])
            with transaction.atomic():
                user = User(username=correo,first_name=nombres,
                            last_name=apellidos,email=correo,userTipo=tipo,userFoto=foto)
                user.save()
                rol=Group.objects.get(pk=idRol)
                user.groups.add(rol)
                if(rol.name == "Administrador"):
                    user.is_staff=True
                user.save()
                passwordGenerado = generarPassword()
                print(f"password {passwordGenerado}")
                user.set_password(passwordGenerado)
                user.save()
                
                mensaje = "Usuario agregado correctamente"
                retorno = {"mensaje":mensaje}
                
                #enviar correo al usuario
                asunto= 'Registro Sistema Mesa de Servicio CTPI-CAUCA'
                mensaje = f'Cordial saludo, <b>{user.first_name} {user.last_name}</b>, nos permitimos \
                    informarle que usted ha sido registrado en el Sistema de Mesa de Servicio \
                    del Centro de Teleinformática y Producción Industrial CTPI de la ciudad de Popayán, \
                    con el Rol: <b>{rol.name}</b>. \
                    <br>Nos permitimos enviarle las credenciales de Ingreso a nuestro sistema.<br>\
                    <br><b>Username: </b> {user.username}\
                    <br><b>Password: </b> {passwordGenerado}\
                    <br><br>Lo invitamos a utilizar el aplicativo, donde podrá usted \
                    realizar solicitudes a la mesa de servicio del Centro. Url del aplicativo: \
                    http://mesadeservicioctpi.sena.edu.co.'
                thread=threading.Thread(
                    target=enviarCorreo, args=(asunto,mensaje,[user.email]))
                thread.start()
                return redirect("/vistaGestionarUsuarios/",retorno)
                
        except Error as error:
            transaction.rollback()
            mensaje= f"{error}"
        retorno = {"mensaje":mensaje}
        return render(request, "administrador/frmRegistrarUsuario.html",retorno)
    else:
        mensaje="Debe iniciar sesion"
        return render(request,"frmIniciarSesion.html",{"mensaje":mensaje})

def generarPassword():
    longitud=10
    caracteres= string.ascii_lowercase + \
        string.ascii_uppercase + string.digits + string.punctuation
    password= ''
    
    for i in range(longitud):
        password += ''.join(random.choice(caracteres))
    return password

def recuperarClave(request):
    try:
        correo = request.POST['txtCorreo']
        user = User.objects.filter(email=correo).first()
        if (user):
            passwordGenerado = generarPassword()
            user.set_password(passwordGenerado)
            user.save()
            mensaje = "Contraseña Actualiza Correctamente y enviada al Correo Electrónico"
            retorno = {"mensaje": mensaje}
            asunto = 'Recuperación de Contraseña Sistema Mesa de Servicio CTPI-CAUCA'
            mensaje = f'Cordial saludo, <b>{user.first_name} {user.last_name}</b>, nos permitimos \
                    informarle que se ha generado nueva contraseña para ingreso al sistema. \
                    <br><b>Username: </b> {user.username}\
                    <br><b>Password: </b> {passwordGenerado}\
                    <br><br>Para comprobar ingresar al sistema haciendo uso de la nueva contraseña.'
            thread = threading.Thread(
                target=enviarCorreo, args=(asunto, mensaje, [user.email]))
            thread.start()
        else:
            mensaje = "No existe usuario con correo ingresado. Revisar"
            retorno = {"mensaje": mensaje}
    except Error as error:
        mensaje = str(error)

    return render(request, 'frmIniciarSesion.html', retorno)

# vistas de la api
class OficinaAmbienteList(generics.ListCreateAPIView):
    queryset = OficinaAmbiente.objects.all()
    serializer_class = OficinaAmbienteSerializer

class OficinaAmbienteDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = OficinaAmbiente.objects.all()
    serializer_class = OficinaAmbienteSerializer



def salir(request):
    auth.logout(request)
    return render(request,"frmIniciarSesion.html",
                  {"mensaje":"Ha cerrado la sesion"})
    
    
def estadisticas(request):
    import matplotlib
    if request.user.is_authenticated:
        matplotlib.use('agg')
        listaAmbientes = OficinaAmbiente.objects.all()
        listaSolicitudes = Solicitud.objects.all()

        # grafico cantidad solicitudes por ambiente
        solicitudesPorAmbiente = Solicitud.objects.values('solOficinaAmbiente')\
            .annotate(cantidad=Count('id'))
        xAmbiente = []
        yCantidadAmbiente = []
        for ambiente in listaAmbientes:
            for solicitud in listaSolicitudes:
                if ambiente.id == solicitud.solOficinaAmbiente.id:
                    xAmbiente.append(ambiente)
                    yCantidadAmbiente.append(0)
                    break
        i = 0
        colores = []
        for ambiente in xAmbiente:
            for solicitud in listaSolicitudes:
                if ambiente.id == solicitud.solOficinaAmbiente.id:
                    yCantidadAmbiente[i] += 1
                    color = "#" + \
                        ''.join([random.choice('0123456789ABCDEF')
                                for j in range(6)])
                    colores.append(color)
            i += 1
        textprops = {"fontsize": 6}
        plt.title("Cantidad de Solicitudes Realizadas \n por Ambiente")
        plt.pie(yCantidadAmbiente, labels=xAmbiente,
                autopct="%0.1f %%", textprops=textprops, colors=colores)
        rutaImagen = os.path.join(settings.MEDIA_ROOT + "\\" + "grafica1.png")
        plt.savefig(rutaImagen)
        plt.close()

        # grafica cantidad solicitudes por mes
        solicitudesPorMes = Solicitud.objects.values(mes=ExtractMonth('fechaHoraCreacion'))\
            .annotate(cantidad=Count('id'))
        yCantidadMes = []
        meses = []
        textoMes = ['Enero', 'Febrero', 'Marzo',
                    'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto']
        colores = []
        for solicitud in solicitudesPorMes:
            if solicitud['mes'] is not None:
                meses.append(textoMes[solicitud['mes']-1])
                yCantidadMes.append(solicitud['cantidad'])
                color = "#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                colores.append(color)
            else:
        # handle the case where solicitud['mes'] is None
        # for example, you could append a default value to meses and yCantidadMes
                meses.append('Unknown')
                yCantidadMes.append(0)

        textprops = {"fontsize": 10}
        plt.title("Cantidad de Solicitudes Realizadas \n por Mes")
        plt.bar(meses, yCantidadMes, color=colores)
        rutaImagen = os.path.join(settings.MEDIA_ROOT + "\\" + "grafica2.png")
        plt.savefig(rutaImagen)
        plt.close()

        # grafico cantidad de casos atentidos por tipo
        '''
        casosPorTipo = SolucionCasoTipoProcedimientos.objects.values(tipo='solTipoProcedimiento__tipNombre')\
            .annotate(cantidad=Count('solSolucionCaso__id'))

        yCantidadCasosTipo = []
        tiposProcedimientos = []

        tipos = TipoProcedimiento.objects.all()
        for tipo in tipos:
            tiposProcedimientos.append(tipo)
            yCantidadCasosTipo.append(0)

        i = 0
        for caso in casosPorTipo:
            for tipo in tipos:
                if caso['tipo'] == tipo.tipNombre:
                    yCantidadCasosTipo[i] += 1
                    color = "#" + \
                        ''.join([random.choice('0123456789ABCDEF')
                                for j in range(6)])
                    colores.append(color)
            i += 1

        textprops = {"fontsize": 6}
        plt.title("Cantidad de Casos Atendidos \n por Tipo Procedimiento")
        plt.bar(tiposProcedimientos, yCantidadCasosTipo, color=colores)
        rutaImagen = os.path.join(settings.MEDIA_ROOT + "\\" + "grafica3.png")
        plt.savefig(rutaImagen)
        plt.close()
        '''
        # generarPdfDevoluciones(meses, yCantidadMes)
        return render(request, "administrador/reportesEstadisticos.html")

    else:
        mensaje = "Debe iniciar sesión"
        return render(request, "frmIniciarSesion.html", {"mensaje": mensaje})
        # acceso a la API


def generarPdfSolicitudes(request):
    # importamos el archivo que puede generar el pdf
    from appMesaServicio.pdfSolicitudes import Pdf
    # obtenemos los datos de las solicitudes
    solicitudes = Solicitud.objects.all()
    # crear un objeto de tipo Pdf que viene de la clase
    # creada en el archivo pdfSolicitudes.py
    doc = Pdf()
    # permite colocar número de página en el pdf
    doc.alias_nb_pages()
    # agrega una pagpina
    doc.add_page()
    # configura letra negrilla tamaño 12
    doc.set_font("Arial", "B", 12)
    # se llama al método mostrarDatos del objeto y se le
    # pasan las solicitudes
    doc.mostrarDatos(solicitudes)
    # exporta el pdf y lo guarda en la carpeta media
    doc.output(f'media/solicitudes.pdf')
    # retorna a un html para mostrarlo
    return render(request, "administrador/mostrarPdf.html")