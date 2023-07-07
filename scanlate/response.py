from rest_framework.response import Response


class ScanlateResponse(Response):
    def __init__(self, msg='', content=None, props=None, *args, **kwargs):
        data = {
            'errors': {},
            'msg': msg,
            'content': content or [],
            'props': props or {},
        }
        super().__init__(data, *args, **kwargs)
