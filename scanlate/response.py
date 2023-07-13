from rest_framework.response import Response


class ScanlateResponse(Response):
    def __init__(self, errors=None, msg='', content=None, props=None, *args, **kwargs):
        data = {
            'errors': errors or {},
            'msg': msg,
            'content': content or [],
            'props': props or {},
        }
        super().__init__(data, *args, **kwargs)
