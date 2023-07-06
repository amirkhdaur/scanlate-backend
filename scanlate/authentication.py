from rest_framework.authentication import TokenAuthentication


class ScanlateTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'
