from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect


def home_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


urlpatterns = [
    path("", home_view, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("api/license/", include("licensing.urls")),
]