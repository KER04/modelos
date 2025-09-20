from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import TipoCategoria, Marca, Prestamo, Producto
from .serializers import (
    TipoCategoriaSerializer, MarcaSerializer, PrestamoSerializer,
    ProductoSerializer, OperacionStockSerializer,
)
from rest_framework.parsers import MultiPartParser, FormParser

# ---- ViewSets CRUD de catálogos ----

class TipoCategoriaViewSet(viewsets.ModelViewSet):
    queryset = TipoCategoria.objects.all().order_by("tipr_nombre")
    serializer_class = TipoCategoriaSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["tipr_nombre"]
    ordering_fields = ["tipr_nombre"]


class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all().order_by("marca_nombre")
    serializer_class = MarcaSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["marca_nombre"]
    ordering_fields = ["marca_nombre"]


class PrestamoViewSet(viewsets.ModelViewSet):
    queryset = Prestamo.objects.all().order_by("pres_nombre")
    serializer_class = PrestamoSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["pres_nombre", "tipo_prestamo"]
    ordering_fields = ["pres_nombre"]


# ---- ViewSet de Producto con acciones de inventario ----

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = (
        Producto.objects
        .select_related("tipo_categoria", "marca", "prestamo")
        .all()
        .order_by("prod_nombre")
    )
    serializer_class = ProductoSerializer
    parser_classes = (MultiPartParser, FormParser)

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "prod_estado",
        "tipo_categoria__tipr_nombre",
        "marca__marca_nombre",
        "prestamo__pres_nombre",
    ]
    search_fields = [
        "prod_nombre", "prod_modelo",
        "marca__marca_nombre",
        "tipo_categoria__tipr_nombre",
        "prestamo__pres_nombre",
    ]
    ordering_fields = [
        "prod_nombre", "prod_valor_unitario",
        # OJO: estas son CharField en tu modelo, el orden será lexicográfico
        "prod_cantidad_disponible", "prod_cantidad_total",
    ]

    def _to_int(self, s):
        try:
            return int(str(s or "0").strip())
        except Exception:
            return 0

    # POST /productos/{id}/prestar/  { "cantidad": 3 }
    @action(detail=True, methods=["post"])
    def prestar(self, request, pk=None):
        producto = self.get_object()
        ser = OperacionStockSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        cantidad = ser.validated_data["cantidad"]

        with transaction.atomic():
            disp = self._to_int(producto.prod_cantidad_disponible)
            prest = self._to_int(producto.prod_cantidad_prestada)
            total = self._to_int(producto.prod_cantidad_total)

            if cantidad > disp:
                return Response(
                    {"detail": f"No hay suficiente stock. Disponible: {disp}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            disp -= cantidad
            prest += cantidad
            # total siempre = disp + prest
            total = disp + prest

            producto.prod_cantidad_disponible = str(disp)
            producto.prod_cantidad_prestada = str(prest)
            producto.prod_cantidad_total = str(total)
            if disp == 0:
                producto.prod_estado = "agotado"
            producto.save()

        return Response(ProductoSerializer(producto).data, status=status.HTTP_200_OK)

    # POST /productos/{id}/devolver/  { "cantidad": 2 }
    @action(detail=True, methods=["post"])
    def devolver(self, request, pk=None):
        producto = self.get_object()
        ser = OperacionStockSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        cantidad = ser.validated_data["cantidad"]

        with transaction.atomic():
            disp = self._to_int(producto.prod_cantidad_disponible)
            prest = self._to_int(producto.prod_cantidad_prestada)
            total = self._to_int(producto.prod_cantidad_total)

            if cantidad > prest:
                return Response(
                    {"detail": f"No puedes devolver más de lo prestado. Prestado: {prest}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            disp += cantidad
            prest -= cantidad
            total = disp + prest

            producto.prod_cantidad_disponible = str(disp)
            producto.prod_cantidad_prestada = str(prest)
            producto.prod_cantidad_total = str(total)
            if disp > 0 and producto.prod_estado in (None, "", " ", "agotado", "sin_stock"):
                producto.prod_estado = "activo"
            producto.save()

        return Response(ProductoSerializer(producto).data, status=status.HTTP_200_OK)
