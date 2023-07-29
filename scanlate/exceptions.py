from rest_framework.views import exception_handler
from .response import ScanlateResponse


def scanlate_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response:
        msg = ''
        if isinstance(response.data, dict):
            msg = response.data.pop('detail', '')

        return ScanlateResponse(errors=response.data, msg=msg, status=response.status_code)
    return response
