from django.utils.cache import add_never_cache_headers

class NoCacheMiddleware:
    """
    Middleware to prevent the browser from caching pages when a user is logged in.
    This ensures that when a user logs out and clicks the browser's "Back" button, 
    they cannot see the cached authenticated pages (like the dashboard).
    Unauthenticated pages are allowed to cache normally for regular browser "Back" behavior.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only prevent caching for authenticated users
        # This protects dashboard data while allowing normal "Back" functionality on public pages
        if hasattr(request, 'user') and request.user.is_authenticated:
            # We don't want to prevent caching for static/media files
            if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
                add_never_cache_headers(response)
                
        return response
