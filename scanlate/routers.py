from rest_framework.routers import SimpleRouter


class ScanlateRouter(SimpleRouter):
    def __init__(self):
        super().__init__()
        self.trailing_slash = '/?'
