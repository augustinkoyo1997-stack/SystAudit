from django.urls import path

from .views import fedapay_return, fedapay_webhook, pricing_view, start_premium_checkout

urlpatterns = [
    path("pricing/", pricing_view, name="pricing"),
    path("checkout/premium/", start_premium_checkout, name="start_premium_checkout"),
    path("return/", fedapay_return, name="fedapay_return"),
    path("webhook/fedapay/", fedapay_webhook, name="fedapay_webhook"),
]
