from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse


def rate_limit(key, limit, window_seconds):
    """Per-IP fixed-window throttle backed by Django's cache framework.

    Counts are per gunicorn worker process (default cache is in-memory),
    so the real ceiling is roughly limit * worker_count — fine for
    deterring casual abuse on a low-traffic site.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            cache_key = f'ratelimit:{key}:{ip}'
            count = cache.get(cache_key, 0)
            if count >= limit:
                return HttpResponse('Too many requests, slow down.', status=429)
            cache.set(cache_key, count + 1, timeout=window_seconds)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
