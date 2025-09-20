from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from .models import TipoCategoria, Marca, Prestamo, Producto


# ---- Serializers base para catálogos ----

class TipoCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCategoria
        fields = ["tipr_id", "tipr_nombre"]


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ["marca_id", "marca_nombre"]


class PrestamoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prestamo
        fields = ["pres_id", "pres_nombre", "tipo_prestamo"]


# ---- Helpers internos ----

def _to_int(value, field_name):
    """
    Convierte cualquier entrada a entero >= 0.
    Si viene vacío/None, lo trata como 0.
    Lanza ValidationError si no es convertible o es negativo.
    """
    if value in (None, "", " "):
        return 0
    try:
        ivalue = int(str(value).strip())
    except (ValueError, TypeError):
        raise serializers.ValidationError({field_name: "Debe ser un entero válido."})
    if ivalue < 0:
        raise serializers.ValidationError({field_name: "No puede ser negativo."})
    return ivalue


def _to_decimal_str(value, field_name):
    """
    Convierte a Decimal (>=0) y devuelve string normalizado, ya que tu modelo
    almacena prod_valor_unitario como CharField.
    """
    if value in (None, "", " "):
        raise serializers.ValidationError({field_name: "Es obligatorio."})
    try:
        d = Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        raise serializers.ValidationError({field_name: "Debe ser numérico."})
    if d < 0:
        raise serializers.ValidationError({field_name: "No puede ser negativo."})
    # normalizamos a string (sin notación científica)
    return format(d, "f")


# ---- Serializer de Producto con dropdowns ----

class ProductoSerializer(serializers.ModelSerializer):
    # Dropdowns (DRF enviará los IDs seleccionados)
    tipo_categoria = serializers.PrimaryKeyRelatedField(
        queryset=TipoCategoria.objects.all().order_by("tipr_nombre")
    )
    marca = serializers.PrimaryKeyRelatedField(
        queryset=Marca.objects.all().order_by("marca_nombre")
    )
    prestamo = serializers.PrimaryKeyRelatedField(
        queryset=Prestamo.objects.all().order_by("pres_nombre")
    )

    # Lectura amigable (solo lectura)
    tipo_categoria_nombre = serializers.SerializerMethodField(read_only=True)
    marca_nombre = serializers.SerializerMethodField(read_only=True)
    prestamo_nombre = serializers.SerializerMethodField(read_only=True)

    # Otros campos
    prod_foto = serializers.ImageField(required=False, allow_null=True)
    prod_cantidad_disponible = serializers.IntegerField(required=False, min_value=0)
    prod_cantidad_prestada = serializers.IntegerField(required=False, min_value=0)
    prod_cantidad_total = serializers.IntegerField(required=False, min_value=0)
    prod_valor_unitario = serializers.CharField()

    class Meta:
        model = Producto
        fields = [
            "prod_id",
            "prod_nombre",
            "prod_modelo",
            "prod_foto",
            "prod_valor_unitario",
            "tipo_prestamos",
            "prod_estado",
            "prod_cantidad_disponible",
            "prod_cantidad_prestada",
            "prod_cantidad_total",
            # FK por dropdown:
            "tipo_categoria", "marca", "prestamo",
            # nombres solo-lectura (para listar bonito):
            "tipo_categoria_nombre", "marca_nombre", "prestamo_nombre",
        ]

    # ---- getters de nombres ----
    def get_tipo_categoria_nombre(self, obj):
        return obj.tipo_categoria.tipr_nombre if obj.tipo_categoria else None

    def get_marca_nombre(self, obj):
        return obj.marca.marca_nombre if obj.marca else None

    def get_prestamo_nombre(self, obj):
        return obj.prestamo.pres_nombre if obj.prestamo else None

    # -------- Validación de reglas de inventario --------
    def validate(self, attrs):
        # Normalizar valor unitario
        if "prod_valor_unitario" in attrs:
            attrs["prod_valor_unitario"] = _to_decimal_str(
                attrs["prod_valor_unitario"], "prod_valor_unitario"
            )

        # Asegurar consistencia de cantidades
        disp = _to_int(
            attrs.get("prod_cantidad_disponible", self._current_int("prod_cantidad_disponible")),
            "prod_cantidad_disponible",
        )
        pres = _to_int(
            attrs.get("prod_cantidad_prestada", self._current_int("prod_cantidad_prestada")),
            "prod_cantidad_prestada",
        )
        total = attrs.get("prod_cantidad_total", None)
        total = _to_int(total, "prod_cantidad_total") if total is not None else disp + pres

        if pres > total:
            raise serializers.ValidationError({"prod_cantidad_prestada": "No puede superar el total."})
        if disp + pres != total:
            total = disp + pres  # regla del sistema

        # Guardar de regreso (enteros; luego convertimos a str para el modelo)
        attrs["prod_cantidad_disponible"] = disp
        attrs["prod_cantidad_prestada"] = pres
        attrs["prod_cantidad_total"] = total

        # Auto-estado útil (opcional)
        estado = attrs.get("prod_estado", None)
        if estado in (None, "", " "):
            if total == 0:
                attrs["prod_estado"] = "sin_stock"
            elif disp == 0:
                attrs["prod_estado"] = "agotado"
            else:
                attrs["prod_estado"] = "activo"

        return attrs

    def _current_int(self, field_name):
        """Obtiene el valor entero actual del instance (si existe)."""
        if not getattr(self, "instance", None):
            return 0
        raw = getattr(self.instance, field_name, "0") or "0"
        return _to_int(raw, field_name)

    # -------- create / update --------
    # Dejamos que ModelSerializer maneje las FKs (por los dropdowns).
    # Solo convertimos las cantidades a string porque el modelo las guarda en CharField.
    def create(self, validated_data):
        for f in ("prod_cantidad_disponible", "prod_cantidad_prestada", "prod_cantidad_total"):
            if f in validated_data:
                validated_data[f] = str(validated_data[f])
        return Producto.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for f in ("prod_cantidad_disponible", "prod_cantidad_prestada", "prod_cantidad_total"):
            if f in validated_data:
                validated_data[f] = str(validated_data[f])
        return super().update(instance, validated_data)


# ---- Serializers para acciones de inventario ----

class OperacionStockSerializer(serializers.Serializer):
    cantidad = serializers.IntegerField(min_value=1)

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que 0.")
        return value
