import httpx


class RutrackerApiError(BaseException):
    ...


class RutrackerRequestError(RutrackerApiError):

    def __init__(self, response: httpx.Response, info: str = '...') -> None:
        super().__init__(f'Response status code: "{response.status_code}". Extra info: "{info}"')
        self.info = info
        self.response = response


class RutrackerSearchSessionExpired(RutrackerRequestError):
    ...
