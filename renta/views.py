# app/views.py
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Renta, TipoPago, Estado, Pago, RentaProducto
from .serializers import (
    RentaSerializer,
    TipoPagoSerializer,
    EstadoSerializer,
    PagoSerializer,
    RentaProductoSerializer,
    RentaReadSerializer,
    PagoReadSerializer,
    RentaProductoReadSerializer,
)


class RentaViewSet(viewsets.ModelViewSet):
    queryset = Renta.objects.select_related("usuario").all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["usuario__username"]  # ajusta según tu modelo Usuario
    ordering_fields = ["renta_fecha_prestamo", "renta_fecha_devolucion", "rent_id"]

    def get_serializer_class(self):
        # Para GET devolvemos la versión “read”, para escritura la básica
        if self.action in ["list", "retrieve"]:
            return RentaReadSerializer
        return RentaSerializer

    @action(detail=True, methods=["get"])
    def pagos(self, request, pk=None):
        """/rentas/{id}/pagos/ -> lista los pagos de una renta"""
        renta = self.get_object()
        qs = renta.pagos.select_related("tipo_pago", "estado", "renta").all()
        serializer = PagoReadSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def productos(self, request, pk=None):
        """/rentas/{id}/productos/ -> productos asociados a la renta"""
        renta = self.get_object()
        qs = renta.renta_productos.select_related(
            "producto", "tipo_categoria", "marca", "prestamo", "renta"
        ).all()
        serializer = RentaProductoReadSerializer(qs, many=True)
        return Response(serializer.data)


class TipoPagoViewSet(viewsets.ModelViewSet):
    queryset = TipoPago.objects.all()
    serializer_class = TipoPagoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["tipa_nombre"]
    ordering_fields = ["tipa_nombre", "tipa_id"]


class EstadoViewSet(viewsets.ModelViewSet):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["esta_nombre"]
    ordering_fields = ["esta_nombre", "esta_id"]


class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.select_related(
        "tipo_pago", "estado", "renta", "renta__usuario"
    ).all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    # ajusta los search_fields según lo que tenga sentido en tu dominio
    search_fields = [
        "renta__usuario__username",
        "tipo_pago__tipa_nombre",
        "estado__esta_nombre",
    ]
    ordering_fields = ["pago_fecha_facturacion", "pago_total", "pago_id"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return PagoReadSerializer
        return PagoSerializer


class RentaProductoViewSet(viewsets.ModelViewSet):
    queryset = RentaProducto.objects.select_related(
        "renta", "producto", "tipo_categoria", "marca", "prestamo"
    ).all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "renta__usuario__username",
        "producto__prod_nombre",  # ajusta al campo real
        "tipo_categoria__tipr_nombre",  # ajusta al campo real
        "marca__marca_nombre",  # ajusta al campo real
    ]
    ordering_fields = ["renta__rent_id", "producto__id"]  # ajusta al campo real

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RentaProductoReadSerializer
        return RentaProductoSerializer
