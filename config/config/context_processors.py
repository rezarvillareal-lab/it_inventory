from django.conf import settings


def auto_logout(request):
    """Expose AUTO_LOGOUT_DELAY and LOGOUT_REDIRECT_URL to templates."""
    return {
        'AUTO_LOGOUT_DELAY': getattr(settings, 'AUTO_LOGOUT_DELAY', 180),
        'LOGOUT_REDIRECT_URL': getattr(settings, 'LOGOUT_REDIRECT_URL', '/login/'),
    }
