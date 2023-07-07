import json
from rest_framework.views import exception_handler


def scanlate_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response:
        errors = {}
        for key in response.data.copy():
            errors[key] = response.data.pop(key)

        response.data['errors'] = errors
        response.data['content'] = []
        response.data['props'] = {}

    return response
