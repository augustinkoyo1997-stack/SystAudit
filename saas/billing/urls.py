from django.urls import path

from .views import fedapay_return, fedapay_webhook, start_premium_checkout

urlpatterns = [
    path("checkout/premium/", start_premium_checkout, name="start_premium_checkout"),
    path("return/", fedapay_return, name="fedapay_return"),
    path("webhook/fedapay/", fedapay_webhook, name="fedapay_webhook"),
]
