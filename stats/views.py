from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import UploadReporteForm
from .ArmaStats_AsistenciaScript import armastats, zrasistencia, procesar_rpt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Miembro, Asistencia, Mision
from datetime import datetime, timedelta
from django.views.generic.list import ListView


def index_view(request):
    return render(request, 'stats/index.html', {})

# TODO hacer esta función más linda
def upload_file(request):
    if request.method == 'POST':
        form = UploadReporteForm(request.POST, request.FILES)
        if form.is_valid():
            mision = Mision(reporte=request.FILES['file'])
            mision.nombre = "Test"
            mision.tipo = "Otros"
            mision.nombre_campa = "Campaña"
            mision.fecha = datetime.today().strftime('%Y-%m-%d')
            mision.save()
            #file = request.FILES['file']
            #path = default_storage.save(str(mision.mision), ContentFile(mision.mision.read()))
            #dict = zrasistencia.main_django(mision.mision.path)
            #dict = armastats.main(mision.mision.path)
            dict = procesar_rpt.main(mision.reporte.path)
            miembros = Miembro.objects.all()

            print("Comienza analisis-----")
            for miembro in miembros:  # miembro de la lista de la DB
                asiste = Asistencia()
                asiste.mision = mision
                asiste.miembro = miembro
                asiste.fecha = datetime.today().strftime('%Y-%m-%d')
                asiste.asistencia = 'Falta'
                t = datetime.strptime("0:0:0", '%H:%M:%S')
                delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
                asiste.tiempo_de_sesion = delta
                asiste.save()
                #print("Estoy en miembro: "+miembro.nombre)
                for jugador, asistencia in dict.items():  # el dict retornado por el script
                    #print("Estoy en JUGADOR: " + jugador.split('.', 1)[1])
                    j1 = jugador.split('.', 1)[1]  # toma solo el nombre sin el rango, en el if se pasa a UPPER
                    j2 = miembro.nombre.upper()  # toma el nombre de Miembro y lo pasa a UPPER
                    if j1.upper() == j2:  # si coinciden es que se conectó al server y debo crear un Asistencia
                        asiste = Asistencia.objects.get(miembro=miembro, fecha=datetime.today().strftime('%Y-%m-%d'))
                        print("ENCONTRE A "+j1+" LE PONGO ASISTENCIA")
                        asiste.asistencia = asistencia[1]
                        t = datetime.strptime(asistencia[0], '%H:%M:%S')
                        delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
                        asiste.tiempo_de_sesion = delta
                        #asiste.requiere_atencion = False
                        asiste.save()
            return HttpResponseRedirect('/success/url/')
    else:
        form = UploadReporteForm()
    return render(request, 'stats/upload.html', {'form': form})


class AsistenciaListView(ListView):
    template_name = 'stats/tabla_asistencia.html'
    model = Asistencia
    paginate_by = 100  # if pagination is desired

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['miembros'] = Miembro.objects.all()
        context['reportes'] = Mision.objects.all()
        return context