from django.utils.deprecation import MiddlewareMixin
from twbot.bot import terminat_idel_connection


class IdleConnectionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        terminat_idel_connection()
        if not os.path.isfile('.env'):
            with open('.env', 'w'):pass
            subprocess.run(['bash', 'task/variable.sh'])