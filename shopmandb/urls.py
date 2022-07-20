from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls.static import static
from django.conf import settings


from shopmandb.views import *
from .yasg import *


urlpatterns = [
    # api login urls
    path("product", ProductView.as_view(), name="product"),
    path("product/fruits", FruitsProductListView.as_view(), name="product-fruits"),
    path("order", OrderView.as_view(), name="order"),
    path("order/<int:id>", OrderUpdateView.as_view(), name="order"),
    path("order/identifier", OrderIdentifierView.as_view(), name="order_identifier"),
    path("paymentlog/fruits", FruitsPaymentLogListView.as_view(), name="paymentlog-fruits"),
    path("order/fruits", FruitsOrderListView.as_view(), name="order-fruits"),
    path("order/genetictest", OrderViewForGeneticTest.as_view(), name="order-genetictest"),
    path("box", BoxView.as_view(), name="box"),
    path("mix", MixView.as_view(), name="mix"),
    path("payment_validation", PaymentValidationView.as_view(), name="payment_validation"),
    path("feedback", Feedback.as_view(), name="feedback"),
    path("profile/sub", SubscriptionListView.as_view(), name="subscription_list"),
    path("profile/sub/<int:pk>", SubscriptionDetailView.as_view(), name="subscription_detail"),
    path("plan", PlanView.as_view(), name="plan_update"),
    path("subscription-info", SubscriptionInfoView.as_view(), name="plan_update"),
    path("wms/order", OrderWmsListView.as_view(), name='wms_order'),
    path("wms/order/<identifier>", OrderWmsUpdateView.as_view(), name='wms_order_update'),
    path("wms/sub", SubscriptionWmsAPIView.as_view(), name='wms_subscription'),
    path("shipping/fee", ShippingFeeAPIView.as_view(), name='get_shipping_fee'),
    path("shipping", ShippingAPIView.as_view(), name='get_shipping_fee'),
    path("statistics", StatisticsView.as_view(), name='get_user_statistics'),
    path(
        'swagger<str:format>',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'
    ),
	path(
        'swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
