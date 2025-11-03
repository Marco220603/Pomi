from rest_framework import serializers
from pomi.models.stundent import Student

class VerifyStudentSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=10, required= True)
    phone = serializers.CharField(max_length=9, required= True)
    # Agregamos validación a nuestro API
    def validate(self, data):
        code = data.get('code').strip().lower()
        phone = data.get('phone')
        if not code and not phone:
            raise serializers.ValidationError({'code': 'El código es obligatorio', 'phone': 'El celular es obligatorio'})
        student = None
        try:
            student = Student.objects.get(code_upc = code)
        except Student.DoesNotExist:
            raise serializers.ValidationError({'code': 'Alumno no encontrado'})
        data['student'] = student
        return data