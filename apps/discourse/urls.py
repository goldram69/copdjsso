# from django.contrib.auth.views import LoginView
from django.urls import path
from .views import (
    CustomLoginView,
    DiscourseSSOProviderView,
    DiscourseSSOLoginView,
    index,
)

urlpatterns = [
    #  Use the new login handler
    path("accounts/login/", CustomLoginView.as_view(), name="discourse_login"),
    path(
        "session/sso_provider/",
        DiscourseSSOProviderView.as_view(),
        name="discourse_sso_provider",
    ),
    path(
        "session/sso_login/",
        DiscourseSSOLoginView.as_view(),
        name="discourse_sso_login",
    ),
    # path('discourse/session/sso_provider/', discourse_sso_provider, name='discourse_sso_provider') ,
    path("", index, name="index"),
]
