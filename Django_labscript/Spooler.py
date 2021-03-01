import json
import runmanager.remote
import os
import time
import shutil

remoteClient = runmanager.remote.Client()
recieved_json_folder = R'C:\Users\Rohit_Prasad_Bhatt\Documents\Django_labscript\media\uploads'
executed_json_folder = R'C:\Users\Rohit_Prasad_Bhatt\Documents\Django_labscript\media\uploads\executed'
json_status_folder = R'C:\Users\Rohit_Prasad_Bhatt\Documents\Django_labscript\media\uploads\status'
exp_script_folder = R'C:\Users\Rohit_Prasad_Bhatt\labscript-suite\userlib\labscriptlib\example_apparatus'

def check_json_dict(json_dict):
    return True

def modify_shot_output_folder(job_id):
    defaut_shot_folder = str(remoteClient.get_shot_output_folder())
    modified_shot_folder = (defaut_shot_folder.rsplit('\\',1)[0])+'\\'+job_id
    remoteClient.set_shot_output_folder(modified_shot_folder)

def gen_script_and_globals(json_dict):
    globals_dict = {'user_id':json_dict['user_id'],'shots':json_dict['experiment_0']['shots']}
    remoteClient.set_globals(globals_dict)
    remoteClient.set_globals(globals_dict)
    script_name = 'Experiment_' + globals_dict['user_id'] + '.py'
    exp_script = os.path.join(exp_script_folder, script_name)
    ins_list = json_dict['experiment_0']['instructions']
    func_dict = {'rx':'rx','delay':'delay','measure':'measure'}
    header_path = R'C:\Users\Rohit_Prasad_Bhatt\labscript-suite\userlib\labscriptlib\example_apparatus\header.py'
    code = ''
    try:
        with open(header_path, "r") as header_file:
            code=header_file.read()
    except:
        print('Something wrong. Does path file exists?')

    try:
        with open(exp_script, "w") as script_file:
            script_file.write(code)
    except:
        print('Something wrong. Does path file exists?')

    for i in range(len(ins_list)):
         inst = ins_list[i]
         func_name = func_dict[ins_list[i][0]]
         params = '('+str(ins_list[i][1:])[1:-1]+')'
         code = 'Experiment.'+func_name+params+'\n'
         try:
             with open(exp_script, "a") as script_file:
                 script_file.write(code)
         except:
             print('Something wrong. Does path file exists?')

    code = 'stop(Experiment.t+0.1)'
    try:
        with open(exp_script, "a") as script_file:
            script_file.write(code)
    except:
        print('Something wrong. Does path file exists?')
    remoteClient.set_labscript_file(exp_script) # CAUTION !! This command only selects the file. It does not generate it!
    return exp_script

while True:
    time.sleep(3)
    files = list(fn for fn in next(os.walk(recieved_json_folder))[2])
    if not files:
        continue
    else:
        json_name = (sorted(files))[0]
        job_id = (json_name)[5:-5]
        recieved_json_path = os.path.join(recieved_json_folder, json_name)
        executed_json_path = os.path.join(executed_json_folder, json_name)
        status_file_name = 'status_'+job_id+'.txt'
        status_file_path = os.path.join(json_status_folder, status_file_name)
        with open(recieved_json_path) as file:
            data = json.load(file)
            json_is_fine = check_json_dict(data)
        if json_is_fine:
            with open(status_file_path, 'w') as status_file:
                status_msg = 'Passed json sanity check'
                status_file.write(status_msg)
            exp_script = gen_script_and_globals(data)
            remoteClient.reset_shot_output_folder()
            modify_shot_output_folder(job_id)
            remoteClient.engage()
            with open(status_file_path, 'w') as status_file:
                status_msg = 'Compilation done. Shots sent to BLACS'
                status_file.write(status_msg)
            shutil.move(recieved_json_path, executed_json_path)
            #os.remove(recieved_json_path)
            #os.remove(exp_script)
        else:
            with open(status_file_path, 'w') as status_file:
                status_msg = 'Failed json sanity check. File will be deleted'
                status_file.write(status_msg)
            os.remove(recieved_json_path)
