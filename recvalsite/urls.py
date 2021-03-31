"""recvalsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from media_with_range.urls import media_with_range

urlpatterns = [path("admin/", admin.site.urls), path("", include("validation.urls"))]
# URLs for media files:
urlpatterns.extend(media_with_range())
if settings.DEBUG and settings.USE_DJANGO_DEBUG_TOOLBAR:
    import debug_toolbar

    # necessary for debug_toolbar to work
    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
