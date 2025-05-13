"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from .views import home
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from apps.discourse.views import CustomLoginView  # Import your custom login view


def home(request):
    return HttpResponse("Welcome to the homepage!")


urlpatterns = [
    path('admin/', admin.site.urls),
    #path("accounts/login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    #path("account/login/", LoginView.as_view(template_name="registration/login.html"), name="login_alt"),  # ✅ Fix Discourse redirection

    # Include the discourse app URLs with a prefix.
    # If you want all SSO endpoints to be available under /discourse/, do so:
    path('discourse/', include(('apps.discourse.urls', 'discourse'), namespace='discourse')),
    #path("accounts/login/", auth_views.LoginView.as_view(), name="login"),  # ✅ Fix login route

    # Optionally, if you need the SSO endpoints at the root level, you can include them directly
    # path('', include('apps.discourse.urls')),
    path('', home, name='home'),
]
