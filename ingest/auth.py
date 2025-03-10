import os
from functools import wraps
from flask import request, Response

def check_auth(username, password):
    """
    Check if a username/password combination is valid.
    Credentials are read from environment variables.
    """
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "secret")
    return username == admin_username and password == admin_password

def authenticate():
    """Sends a 401 response that enables basic auth."""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials.',
        401,
        {'WWW-Authenticate': 'Basic realm="Admin Area"'}
    )

def requires_auth(f):
    """
    Decorator that prompts for basic auth credentials.
    Use this to protect endpoints that should only be available to the admin.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
