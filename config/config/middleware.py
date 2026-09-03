import time
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.conf import settings as django_settings


class AutoLogoutMiddleware:
    """
    Middleware to automatically log out users after a period of inactivity.
    Stores last activity timestamp in `request.session['last_activity']`.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, 'AUTO_LOGOUT_DELAY', 180)

    def __call__(self, request):
        try:
            if request.user.is_authenticated:
                last_activity = request.session.get('last_activity')
                now = int(time.time())
                if last_activity and (now - last_activity) > self.timeout:
                    # logout and clear session when timed out
                    logout(request)
                    request.session.flush()
                    # immediately redirect to logout/login page
                    redirect_to = getattr(django_settings, 'LOGOUT_REDIRECT_URL', None) or getattr(django_settings, 'LOGIN_URL', '/')
                    return redirect(redirect_to)
                else:
                    # update last activity timestamp
                    request.session['last_activity'] = now
        except Exception:
            # don't break requests if middleware fails
            pass

        response = self.get_response(request)
        return response
