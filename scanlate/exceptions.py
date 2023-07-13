from rest_framework.views import exception_handler
from .response import ScanlateResponse


def scanlate_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response:
        msg = response.data.pop('detail', '')
        return ScanlateResponse(errors=response.data, msg=msg)
    return response
