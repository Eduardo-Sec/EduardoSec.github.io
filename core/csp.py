import secrets


class ContentSecurityPolicyMiddleware:
    """Generates a per-request nonce for inline <script> tags and sets a
    strict CSP header. Templates access the nonce via request.csp_nonce
    (available without a context processor since django.template.context_
    processors.request is already enabled)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)

        policy = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{request.csp_nonce}' https://unpkg.com; "
            # unsafe-inline here (not on script-src) because the custom
            # cursor in main.js sets element.style.left/top/transform on
            # every mousemove, which CSP treats the same as a style=""
            # attribute. That's first-party positioning math with zero
            # user-input influence, not a realistic injection vector --
            # the actual XSS protection is script-src staying strict.
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "object-src 'none'"
        )
        response['Content-Security-Policy'] = policy

        # This site never uses any of these browser features -- deny them
        # outright so an XSS or a compromised third-party script couldn't
        # invoke them even if one somehow got past the CSP above.
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), payment=(), usb=(), '
            'magnetometer=(), gyroscope=(), accelerometer=(), interest-cohort=()'
        )
        return response
