from django.shortcuts import render


def page_not_found(request, exception):
    """Ошибка 404."""
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failure(request, reason=''):
    """Ошибка csrf key."""
    return render(request, 'core/403csrf.html')


def no_ability_to_watch(request, reason=''):
    """Ошибка 403 (остутствие прав)."""
    return render(request, 'core/403.html')
