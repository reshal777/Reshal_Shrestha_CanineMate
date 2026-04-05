from django.utils.cache import add_never_cache_headers
from django.http import Http404

class NoCacheMiddleware:
    """
    Only prevent caching on sensitive authenticated pages (dashboard, profile, admin, payments).
    Public pages and regular browsing pages cache normally so the back button works correctly.
    """
    # Only these URL prefixes need no-cache protection
    SENSITIVE_PATHS = (
        '/dashboard',
        '/profile',
        '/admin/',
        '/payment',
        '/checkout',
        '/cart',
        '/logout',
        '/accounts/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (hasattr(request, 'user') and request.user.is_authenticated
                and not request.path.startswith('/static/')
                and not request.path.startswith('/media/')
                and any(request.path.startswith(p) for p in self.SENSITIVE_PATHS)):
            add_never_cache_headers(response)

        return response

class Admin404Middleware:
    """
    Middleware that returns a 404 Page Not Found error for /admin/ paths
    unless the user is authenticated as staff. This effectively hides the
    admin URL from unauthorized users entirely.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If accessing /admin/ and the user is NOT staff, hide it with a 404
        if request.path.startswith('/admin/') and not (request.user.is_authenticated and request.user.is_staff):
            raise Http404
            
        return self.get_response(request)
