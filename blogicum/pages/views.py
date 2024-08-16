from django.shortcuts import render
from django.http import HttpResponseForbidden


def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    return render(request, 'pages/500.html', status=500)


def csrf_failure(request, reason='', exception=None):
    if exception is not None:
        return HttpResponseForbidden("Ошибка CSRF: доступ запрещен.")
    return render(request, 'pages/403csrf.html', status=403)
