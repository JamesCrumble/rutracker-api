from functools import wraps
from fastapi import HTTPException, status

from ..rutracker_api.exceptions import RutrackerRequestError, RutrackerSearchSessionExpired


def wrap_to_http_exc(func):

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RutrackerSearchSessionExpired as exc:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail=exc.info)
        except RutrackerRequestError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return wrapper
