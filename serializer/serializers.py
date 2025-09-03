# Imports:
from rest_framework import serializers
from django.contrib.auth.models import User
from apps.autenticacion.models import *
from django.contrib.auth import get_user_model
Usuario = get_user_model()

# REGISTRO
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'promedio', 'disponibilidad']

    def create(self, validated_data):
        user = Usuario.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
            promedio=validated_data.get('promedio', None),
            disponibilidad=validated_data.get('disponibilidad', True),
        )

        rol_usuario, created = Rol.objects.get_or_create(nombre='Usuario')
        UsuarioRol.objects.create(usuario=user, rol=rol_usuario)

        return user

# USUARIO
class UsuarioSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    rol_id = serializers.IntegerField(source='rol.id', read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'promedio', 'disponibilidad',
            'rol_id', 'rol_nombre', 'roles'
        ]

    def get_roles(self, obj):
        from apps.autenticacion.models import UsuarioRol  # evita import circular
        asignaciones = UsuarioRol.objects.filter(usuario=obj).select_related('rol')
        return [
            {
                "id": ar.rol.id,
                "nombre": ar.rol.nombre
            }
            for ar in asignaciones
        ]

# LOGIN
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

# ROL SIMPLE
class RolSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre']
# ROL COMPLETO
class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion']

# USUARIO X ROL
class UsuarioRolSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all())
    rol = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all())

    class Meta:
        model = UsuarioRol
        fields = ['id', 'usuario', 'rol', 'asignado_en']

#RECURSO
class RecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recurso
        fields = ['id', 'nombre', 'url']

#RECURSOXROL
class RecursoRolSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecursoRol
        fields = ['id', 'rol', 'recurso', 'asignado_en']

