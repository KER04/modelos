# app/serializers.py
from rest_framework import serializers
from .models import Renta, TipoPago, Estado, Pago, RentaProducto
# Si necesitas mostrar campos de Usuario/Producto/etc., impórtalos también

# ---------- 1) CRUD BÁSICO (FK por ID) ----------
class RentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Renta
        fields = ['rent_id', 'renta_fecha_prestamo', 'renta_fecha_devolucion', 'usuario']


class TipoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoPago
        fields = ['tipa_id', 'tipa_nombre']


class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = ['esta_id', 'esta_nombre']


class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = [
            'pago_id',
            'pago_total', 'pago_descuento', 'pago_total_cancelado',
            'pago_fecha_facturacion', 'pago_fecha_limite_pago',
            'tipo_pago', 'estado', 'renta',
        ]


class RentaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentaProducto
        fields = [
            'renta', 'producto', 'tipo_categoria', 'marca', 'prestamo',
        ]
        # unique_together ya está en el modelo; DRF lo validará a nivel DB.
        # Si quieres validación previa, puedes agregar validate().

    def validate(self, attrs):
        # Validación opcional para evitar duplicados antes de llegar a DB
        renta = attrs.get('renta')
        producto = attrs.get('producto')
        if RentaProducto.objects.filter(renta=renta, producto=producto).exists():
            raise serializers.ValidationError('Este producto ya está vinculado a la renta.')
        return attrs


# ---------- 2) LECTURA EXPANDIDA (solo para GET) ----------
# Útil para mostrar nombres legibles sin complicar el POST/PUT
class RentaReadSerializer(serializers.ModelSerializer):
    usuario_display = serializers.StringRelatedField(source='usuario', read_only=True)
    class Meta:
        model = Renta
        fields = [
            'rent_id', 'renta_fecha_prestamo', 'renta_fecha_devolucion',
            'usuario', 'usuario_display',
        ]


class PagoReadSerializer(serializers.ModelSerializer):
    renta_info = RentaReadSerializer(source='renta', read_only=True)
    tipo_pago_nombre = serializers.StringRelatedField(source='tipo_pago', read_only=True)
    estado_nombre = serializers.StringRelatedField(source='estado', read_only=True)

    class Meta:
        model = Pago
        fields = [
            'pago_id',
            'pago_total', 'pago_descuento', 'pago_total_cancelado',
            'pago_fecha_facturacion', 'pago_fecha_limite_pago',
            'tipo_pago', 'tipo_pago_nombre',
            'estado', 'estado_nombre',
            'renta', 'renta_info',
        ]


class RentaProductoReadSerializer(serializers.ModelSerializer):
    renta_info = RentaReadSerializer(source='renta', read_only=True)
    # Para las demás FK usamos StringRelatedField (requiere __str__ correcto en cada modelo)
    producto_nombre = serializers.StringRelatedField(source='producto', read_only=True)
    tipo_categoria_nombre = serializers.StringRelatedField(source='tipo_categoria', read_only=True)
    marca_nombre = serializers.StringRelatedField(source='marca', read_only=True)
    prestamo_nombre = serializers.StringRelatedField(source='prestamo', read_only=True)

    class Meta:
        model = RentaProducto
        fields = [
            'renta', 'renta_info',
            'producto', 'producto_nombre',
            'tipo_categoria', 'tipo_categoria_nombre',
            'marca', 'marca_nombre',
            'prestamo', 'prestamo_nombre',
        ]
