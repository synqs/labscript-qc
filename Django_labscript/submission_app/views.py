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
config_dict = {'backend_name': 'SYNQS_NaLi_spins_backend',
 'backend_version': '0.0.1',
 'n_qubits': 5,     # number of wires
 'atomic_species': ['na'] ,
 'basis_gates': ['rLx', 'rLz', 'rLz2'],
 'gates': [
    {'name': 'rLz',
     'parameters': ['delta'],
     'qasm_def': 'gate rLz(delta) {}',
     'coupling_map': [[0],[1],[2],[3],[4]],
     'description': 'Evolution under the Z gate'},
     {'name': 'rLz2',
      'parameters': ['chi'],
      'qasm_def': 'gate rLz2(chi) {}',
      'coupling_map': [[0],[1],[2],[3],[4]],
      'description': 'Evolution under the Z2 gate'},
    {'name': 'rLx',
     'parameters': ['omega'],
     'qasm_def': 'gate rx(omega) {}',
     'coupling_map': [[0],[1],[2],[3],[4]],
     'description': 'Evolution under the X gate'}],
 'supported_instructions': ['delay', 'rLx', 'rLz', 'rLz2', 'measure', 'barrier'],
 'local': False,            # backend is local or remote (as seen from user)
 'simulator': False,        # backend is a simulator
 'conditional': False,      # backend supports conditional operations
 'open_pulse': False,       # backend supports open pulse
 'memory': True,            # backend supports memory
 'max_shots': 60,
 'coupling_map': [[]],
 'max_experiments': 3,
 'description': 'Setup of a cold atomic mixtures experiment with qudits.',
 'url': 'http://localhost:9000/shots/',
 'credits_required': False,
 'display_name': 'NaLi'}


result_dict = {
    'backend_name': 'SoPa_atomic_mixtures',
    'backend_version': '0.0.1',
    'job_id': 'None',
    'qobj_id': None,
    'success': True,
    'header': {},
    'results': [
        {
            'header': {'name': 'experiment_blah', 'extra metadata': 'text'},
            'shots': 3,
            'success': True,
            'meas_return': 'single',
            'meas_level': 1,
            'data': {      # slot 1 (Na)      # slot 2 (Li)
                'memory': [[[90012.,  9988.], [5100., 4900.]],  # Shot 1
                           [[89900., 10100.], [5000., 5000.]],  # Shot 2
                           [[90000., 10000.], [5050., 4950.]]]  # Shot 3
            }
        }
    ]
}


@csrf_exempt
def get_config(request):
    if request.method == 'GET':
        return JsonResponse(config_dict)
    else:
        return HttpResponse('Only GET request allowed!')

@csrf_exempt
def post_job(request):
    job_response_dict = {'job_id': 'None','status': 'None','detail': 'None'}
    if request.method == 'POST':
        try:
            data = json.loads(request.POST['json'])
        except:
            job_response_dict['detail'] = 'Error loading json data!'
            return JsonResponse(job_response_dict)
        try:
            dir = R'D:\Django_server_data\uploads'
            os.makedirs(dir, exist_ok=True)
            job_id = (datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S_')) + (uuid.uuid4().hex)[:5]
            json_name = 'file_' + job_id + '.json'
            json_path = os.path.join(dir,json_name)
            with open(json_path, 'w') as f:
                json.dump(data, f)
        except:
            job_response_dict['detail'] = 'Error saving json data!'
            return JsonResponse(job_response_dict)
    else:
        return HttpResponse('Only POST request allowed!')

    job_response_dict['job_id'] = job_id
    job_response_dict['status'] = 'INITIALIZING'
    job_response_dict['detail'] = 'Got your json.'
    json_status_folder = R'D:\Django_server_data\uploads\status'
    status_file_name = 'status_'+job_id+'.json'
    status_file_path = os.path.join(json_status_folder, status_file_name)
    with open(status_file_path, 'w') as status_file:
        json.dump(job_response_dict, status_file)
    return JsonResponse(job_response_dict)

@csrf_exempt
def get_job_status(request):
    status_msg_dict = {'job_id': 'None','status': 'None','detail': 'None'}
    if request.method == 'GET':
        try:
            data = json.loads(request.GET['json'])
            job_id = data['job_id']
            status_msg_dict['job_id'] = job_id
        except:
            status_msg_dict['detail'] = 'Error loading json data!'
            return JsonResponse(status_msg_dict)
        try:
            assert len(job_id)==21
            json_status_folder = R'D:\Django_server_data\uploads\status'
            status_file_name = 'status_'+job_id+'.json'
            status_file_path = os.path.join(json_status_folder, status_file_name)
            with open(status_file_path) as status_file:
                status_msg_dict = json.load(status_file)
        except:
            status_msg_dict['detail'] = 'Error getting status. Maybe invalid JOB ID!'
            return JsonResponse(status_msg_dict)
    else:
        return HttpResponse('Only GET request allowed!')

    return JsonResponse(status_msg_dict)

@csrf_exempt
def get_job_result(request):
    status_msg_dict = {'job_id': 'None','status': 'None','detail': 'None'}
    if request.method == 'GET':
        try:
            data = json.loads(request.GET['json'])
            job_id = data['job_id']
            status_msg_dict['job_id'] = job_id
        except:
            status_msg_dict['detail'] = 'Error loading json data!'
            return JsonResponse(status_msg_dict)
        try:
            assert len(job_id)==21
            json_status_folder = R'D:\Django_server_data\uploads\status'
            status_file_name = 'status_'+job_id+'.json'
            status_file_path = os.path.join(json_status_folder, status_file_name)
            with open(status_file_path) as status_file:
                status_msg_dict = json.load(status_file)
        except:
            status_msg_dict['detail'] = 'Error getting status. Maybe invalid JOB ID!'
            return JsonResponse(status_msg_dict)
        if status_msg_dict['status'] == 'DONE':
            job_id = status_msg_dict['job_id']
            result_dict['job_id'] = job_id
            return JsonResponse(result_dict)
        else:
            return JsonResponse(status_msg_dict)
    else:
        return HttpResponse('Only GET request allowed!')
