import logging
from functools import wraps

def safe_call(default=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                logging.getLogger("safe_call").error(
                    f"{fn.__name__} failed: {e}", exc_info=True
                )
                return default
        return wrapper
    return decorator
