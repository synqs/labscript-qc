#from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.conf import settings
import uuid
import datetime

# Create your views here.
di = {'backend_name': 'atomic_mixtures',
 'backend_version': '0.0.1',
 'n_qubits': 2,     # number of wires
 'atomic_species': ['Na', 'K'] ,
 'basis_gates': ['delay', 'rx'],
 'gates': [
    {'name': 'delay',
     'parameters': ['tau', 'delta'],
     'qasm_def': 'gate delay(tau, delta) {}',
     'coupling_map': [[0, 1]],
     'description': 'evolution under SCC Hamiltonian for time tau'},
    {'name': 'rx',
     'parameters': ['theta'],
     'qasm_def': 'gate rx(theta) {}',
     'coupling_map': [[0]],
     'description': 'Rotation of the sodium spin'}],
 'supported_instructions': ['delay', 'rx', 'measure', 'barrier'],
 'local': False,            # backend is local or remote (as seen from user)
 'simulator': False,        # backend is a simulator
 'conditional': False,      # backend supports conditional operations
 'open_pulse': False,       # backend supports open pulse
 'memory': True,            # backend supports memory
 'max_shots': 60,
 'coupling_map': [[0, 1]],
 'max_experiments': 3,
 'description': 'Setup of an atomic mixtures experiment with one trapping site and two atomic species, namely Na and K.',
 'url': 'http://url_of_the_remote_server',
 'credits_required': False,
 'online_date': 'Since_big_bang',
 'display_name': 'SoPa'}

@csrf_exempt
def config(request):
    if request.method == 'GET':
        return JsonResponse(di)

@csrf_exempt
def upload(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.POST['json'])
            #process the json data
        except:
            return HttpResponse("Error loading json data!")

        #dir = os.path.join(settings.MEDIA_ROOT, "uploads")
        dir = R'C:\Users\Rohit_Prasad_Bhatt\Documents\Django_labscript\media\uploads'
        os.makedirs(dir, exist_ok=True)
        job_id = (datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S_")) + (uuid.uuid4().hex)[:5]
        json_name = 'file_' + job_id + '.json'
        json_path = os.path.join(dir,json_name)
        with open(json_path, 'w') as f:
            json.dump(data, f)

    else:
        return HttpResponseNotFound()

    return HttpResponse("Got your json. Your JOB ID is : "+job_id)

@csrf_exempt
def check_shot_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.POST['json'])
            job_id = data['job_id']
        except:
            return HttpResponse("Error loading JOB ID !")

        json_status_folder = R'C:\Users\Rohit_Prasad_Bhatt\Documents\Django_labscript\media\uploads\status'
        status_file_name = 'status_'+job_id+'.txt'
        status_file_path = os.path.join(json_status_folder, status_file_name)
        try:
            with open(status_file_path, "r") as status_file:
                status_msg = status_file.read()
        except:
            return HttpResponse("Invalid JOB ID !")
    else:
        return HttpResponseNotFound()

    return HttpResponse(status_msg)
