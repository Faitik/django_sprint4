from django.conf import settings
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.conf.urls.static import static
from django.middleware.csrf import CsrfViewMiddleware
from django.shortcuts import render
from django.http import HttpResponseForbidden

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pages/', include('pages.urls', namespace='pages')),
    path('', include('blog.urls', namespace='blog')),
    path('auth/', include('django.contrib.auth.urls')),
    path(
        'registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('blog:index'),
        ),
        name='registration',
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )


def custom_csrf_failure(request, reason="", exception=None):
    return HttpResponseForbidden("Ошибка CSRF: доступ запрещен.")

handler403 = custom_csrf_failure
handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'
