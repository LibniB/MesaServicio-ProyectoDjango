from rest_framework import serializers
from appMesaServicio.models import *

class OficinaAmbienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OficinaAmbiente
        fields = '__all__'
        
