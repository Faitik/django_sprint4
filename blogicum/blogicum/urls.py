from django.conf import settings
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.conf.urls.static import static
from django.conf.urls import handler400, handler403, handler404, handler500
from django.shortcuts import render


# Обработчики ошибок
def custom_csrf_failure(request, reason=""):
    return render(request, 'pages/403csrf.html', status=403)

def custom_page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)

def custom_server_error(request):
    return render(request, 'pages/500.html', status=500)

# Привязка кастомных обработчиков к обработчикам Django
handler403 = custom_csrf_failure
handler404 = custom_page_not_found
handler500 = custom_server_error

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

handler403 = 'pages.views.csrf_failure'
handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'
