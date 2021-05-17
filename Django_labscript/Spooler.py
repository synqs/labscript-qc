import json
import runmanager.remote
import os
import time
import shutil
from jsonschema import validate

remoteClient = runmanager.remote.Client()
recieved_json_folder = R'Y:\uploads'
executed_json_folder = R'Y:\uploads\executed'
json_status_folder = R'Y:\uploads\status'
exp_script_folder = R'C:\Users\Rohit_Prasad_Bhatt\labscript-suite\userlib\labscriptlib\example_apparatus'
num_qudits=5
exper_schema={"type":"object","required":["instructions","shots","num_wires"],
 "properties":{
     "instructions":{"type":"array","items":{"type":"array"}},
     "shots":{"type":"number","minimum":0,"maximum":60},
     "num_wires":{"type":"number","minimum":1,"maximum":num_qudits}
 },
"additionalProperties": False}

rLx_schema = {
  "type": "array",
  "minItems": 3,
  "maxItems": 3,
  "items": [
    {
      "type": "string","enum": ['rLx','rLz','rLz2']
    },
    {
      "type": "array","maxItems": 1,"items": [{"type": "number","minimum": 0,"maximum": (num_qudits-1)}]
    },
    {
      "type": "array","items": [{"type": "number","minimum": 0,"maximum": 6.284}]
    }
  ]
}

barrier_measure_schema = {
  "type": "array",
  "minItems": 3,
  "maxItems": 3,
  "items": [
    {
      "type": "string","enum": ['measure','barrier']
    },
    {
      "type": "array","maxItems": num_qudits,"items": [{"type": "number","minimum": 0,"maximum": (num_qudits-1)}]
    },
    {
      "type": "array","maxItems": 0
    }
  ]
}

def check_with_schema(obj,schm):
    try:
        validate(instance = obj, schema = schm)
        return '',True
    except Exception as e:
        return str(e),False

def check_json_dict(json_dict):
    ins_schema_dict = {'rLx':rLx_schema,'rLz':rLx_schema,'rLz2':rLx_schema,'barrier':barrier_measure_schema, 'measure':barrier_measure_schema}
    max_exps=3
    for e in json_dict:
        err_code='Wrong experiment name or too many experiments'
        try:
            exp_ok = e.startswith('experiment_') and e[11:].isdigit() and (int(e[11:])<=max_exps)
        except:
            exp_ok = False
            break
        if not exp_ok:
            break
        err_code, exp_ok = check_with_schema(json_dict[e], exper_schema)
        if not exp_ok:
            break
        ins_list = json_dict[e]['instructions']
        for ins in ins_list:
            try:
                err_code, exp_ok = check_with_schema(ins, ins_schema_dict[ins[0]])
            except Exception as e:
                err_code='Wrong instruction '+str(e)
                exp_ok = False
            if not exp_ok:
                break
        if not exp_ok:
            break
    return err_code.replace('\n', '..'),exp_ok

def modify_shot_output_folder(new_dir):
    defaut_shot_folder = str(remoteClient.get_shot_output_folder())
    modified_shot_folder = (defaut_shot_folder.rsplit('\\',1)[0])+'\\'+new_dir
    remoteClient.set_shot_output_folder(modified_shot_folder)

def gen_script_and_globals(json_dict,user_id):
    globals_dict = {'user_id':'guest','shots':json_dict[next(iter(json_dict))]['shots']}
    globals_dict['shots'] = 4
    try:
        globals_dict['user_id'] = user_id
    except:
        pass
    remoteClient.set_globals(globals_dict)
    remoteClient.set_globals(globals_dict)
    script_name = 'Experiment_' + globals_dict['user_id'] + '.py'
    exp_script = os.path.join(exp_script_folder, script_name)
    ins_list = json_dict[next(iter(json_dict))]['instructions']
    func_dict = {'rLx':'rLx','rLz2':'rLz2','rLz':'rLz','delay':'delay','measure':'measure','barrier':'barrier'}
    header_path = R'C:\Users\Rohit_Prasad_Bhatt\labscript-suite\userlib\labscriptlib\example_apparatus\header.py'
    code = ''
    try:
        with open(header_path, "r") as header_file:
            code=header_file.read()
    except:
        print('Something wrong. Does header file exists?')

    try:
        with open(exp_script, "w") as script_file:
            script_file.write(code)
    except:
        print('Something wrong. Does file path exists?')

    for i in range(len(ins_list)):
         inst = ins_list[i]
         func_name = func_dict[ins_list[i][0]]
         params = '('+str(ins_list[i][1:])[1:-1]+')'
         code = 'Experiment.'+func_name+params+'\n'
         try:
             with open(exp_script, "a") as script_file:
                 script_file.write(code)
         except:
             print('Something wrong. Does file path exists?')

    code = 'Experiment.final_action()'+'\n'+'stop(Experiment.t+0.1)'
    try:
        with open(exp_script, "a") as script_file:
            script_file.write(code)
    except:
        print('Something wrong. Does file path exists?')
    remoteClient.set_labscript_file(exp_script) # CAUTION !! This command only selects the file. It does not generate it!
    return exp_script

while True:
    time.sleep(3)
    files = list(fn for fn in next(os.walk(recieved_json_folder))[2])
    if not files:
        continue
    else:
        json_name = (sorted(files))[0]
        ji_ui = (json_name)[5:-5]
        job_id, user_id = ji_ui.split('-')
        recieved_json_path = os.path.join(recieved_json_folder, json_name)
        executed_json_path = os.path.join(executed_json_folder, json_name)
        status_file_name = 'status_'+job_id+'.json'
        status_file_path = os.path.join(json_status_folder, status_file_name)
        status_msg_dict = {'job_id': 'None','status': 'None','detail': 'None'}
        with open(recieved_json_path) as file:
            data = json.load(file)
            err_msg, json_is_fine = check_json_dict(data)
        if json_is_fine:
            with open(status_file_path) as status_file:
                status_msg_dict = json.load(status_file)
                status_msg_dict['detail'] += '; Passed json sanity check'
            with open(status_file_path, 'w') as status_file:
                json.dump(status_msg_dict, status_file)
            ##remoteClient.reset_shot_output_folder()
            for exp in data:
                exp_dict = {exp:data[exp]}
                exp_script = gen_script_and_globals(exp_dict,user_id)
                remoteClient.reset_shot_output_folder()
                modify_shot_output_folder(job_id+ '\\' + str(exp))
                remoteClient.engage()#check that this is blocking.
            with open(status_file_path) as status_file:
                status_msg_dict = json.load(status_file)
                status_msg_dict['detail'] += '; Compilation done. Shots sent to BLACS'
                status_msg_dict['status'] = 'RUNNING'
            with open(status_file_path, 'w') as status_file:
                json.dump(status_msg_dict, status_file)
            shutil.move(recieved_json_path, executed_json_path)
            #os.remove(recieved_json_path)
            #os.remove(exp_script)
        else:
            with open(status_file_path) as status_file:
                status_msg_dict = json.load(status_file)
                status_msg_dict['detail'] += '; Failed json sanity check. File will be deleted. Error message : '+err_msg
                status_msg_dict['status'] = 'ERROR'
            with open(status_file_path, 'w') as status_file:
                json.dump(status_msg_dict, status_file)
            os.remove(recieved_json_path)
