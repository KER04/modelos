from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RentaViewSet, TipoPagoViewSet, EstadoViewSet, PagoViewSet, RentaProductoViewSet
)

router = DefaultRouter()
router.register(r'rentas', RentaViewSet, basename='renta')
router.register(r'tipos-pago', TipoPagoViewSet, basename='tipo-pago')
router.register(r'estados', EstadoViewSet, basename='estado')
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'rentas-productos', RentaProductoViewSet, basename='renta-producto')

urlpatterns = [
    path('', include(router.urls)),
]