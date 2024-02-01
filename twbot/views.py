from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.core.management import call_command
from django.core.management import get_commands
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from utils import run_cmd
from background_task import background
from rest_framework import status
from .models import run_command

@method_decorator(csrf_exempt, name='dispatch')
class run_commandss(APIView):
    """ 
    An api view for user registration and return error if these is any error or not provided insufficient data
    """
    def post(self, request, format=None):
        print(request.data)
        data = request.data
        all_comands_li = get_commands()
        
        commandss = run_command.objects.all()
        
        msg = ''
        if 'cmd' in data and data['cmd'] in all_comands_li :
            if data['cmd'] :
                call_command(data['cmd'])
                msg = 'run django command successfully'
        if 'subprocess' in data :
            if data['subprocess'] :
                run_cmd(data['subprocess'])
                msg = 'run command successfully'
        
        if msg :
            return Response({r'msg': msg}, status=status.HTTP_200_OK)
        msg = 'could not found the command'
        return Response({r'msg': msg}, status=status.HTTP_204_NO_CONTENT)