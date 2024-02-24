from django.utils.deprecation import MiddlewareMixin
from twbot.bot import terminat_idel_connection


class IdleConnectionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        terminat_idel_connection()
