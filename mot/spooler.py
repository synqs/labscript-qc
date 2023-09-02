"""
This is the file that creates the labscript file and sends it to the BLACS.
"""
import json
import os
import time
import shutil

import runmanager.remote
from jsonschema import validate
from utils.schemes import ResultDict

remoteClient = runmanager.remote.Client()

# remote files
REMOTE_BASE_PATH = "."
RECEIVED_JSON_FOLDER = f"{REMOTE_BASE_PATH}"
EXECUTED_JSON_FOLDER = f"{REMOTE_BASE_PATH}/executed"
JSON_STATUS_FOLDER = f"{REMOTE_BASE_PATH}/status"

# local files
LOCAL_LABSCRIPT_PATH = "."
EXP_SCRIPT_FOLDER = R"C:\Users\Rohit_Prasad_Bhatt\labscript-suite\userlib\labscriptlib\example_apparatus"
HEADER_PATH = R"C:\Users\Rohit_Prasad_Bhatt\labscript-suite\userlib\
    labscriptlib\example_apparatus\header.py"

NUM_QUDITS = 5

# restrictions and configurations for the json file
exper_schema = {
    "type": "object",
    "required": ["instructions", "shots", "num_wires"],
    "properties": {
        "instructions": {"type": "array", "items": {"type": "array"}},
        "shots": {"type": "number", "minimum": 0, "maximum": 60},
        "num_wires": {"type": "number", "minimum": 1, "maximum": NUM_QUDITS},
    },
    "additionalProperties": False,
}

rLx_schema = {
    "type": "array",
    "minItems": 3,
    "maxItems": 3,
    "items": [
        {"type": "string", "enum": ["rLx", "rLz", "rLz2"]},
        {
            "type": "array",
            "maxItems": 1,
            "items": [{"type": "number", "minimum": 0, "maximum": (NUM_QUDITS - 1)}],
        },
        {
            "type": "array",
            "items": [{"type": "number", "minimum": 0, "maximum": 6.284}],
        },
    ],
}

barrier_measure_schema = {
    "type": "array",
    "minItems": 3,
    "maxItems": 3,
    "items": [
        {"type": "string", "enum": ["measure", "barrier"]},
        {
            "type": "array",
            "maxItems": NUM_QUDITS,
            "items": [{"type": "number", "minimum": 0, "maximum": (NUM_QUDITS - 1)}],
        },
        {"type": "array", "maxItems": 0},
    ],
}


def check_with_schema(obj, schm):
    """
    Performs the check the traditional way.
    """
    # pylint: disable=broad-exception-caught
    try:
        validate(instance=obj, schema=schm)
        return "", True
    except Exception as exc:
        return str(exc), False


def check_json_dict(json_dict):
    """
    This function checks if the json file is valid. This should be fairly
    straightforward to translate into the logic in the `sqooler` project.
    """
    ins_schema_dict = {
        "rLx": rLx_schema,
        "rLz": rLx_schema,
        "rLz2": rLx_schema,
        "barrier": barrier_measure_schema,
        "measure": barrier_measure_schema,
    }
    max_exps = 3
    for exp in json_dict:
        err_code = "Wrong experiment name or too many experiments"
        # pylint: disable=bare-except
        try:
            exp_ok = (
                exp.startswith("experiment_")
                and exp[11:].isdigit()
                and (int(exp[11:]) <= max_exps)
            )
        except:
            exp_ok = False
            break
        if not exp_ok:
            break
        err_code, exp_ok = check_with_schema(json_dict[exp], exper_schema)
        if not exp_ok:
            break
        ins_list = json_dict[exp]["instructions"]
        for ins in ins_list:
            # pylint: disable=broad-exception-caught
            try:
                err_code, exp_ok = check_with_schema(ins, ins_schema_dict[ins[0]])
            except Exception as exc:
                err_code = "Wrong instruction " + str(exc)
                exp_ok = False
            if not exp_ok:
                break
        if not exp_ok:
            break
    return err_code.replace("\n", ".."), exp_ok


def get_file_queue(dir_path: str) -> list:
    """
    A function that returns the list of files in the directory.
    """
    files = list(fn for fn in next(os.walk(dir_path))[2])
    return files


def get_next_job_in_queue(self, backend_name: str) -> dict:
    """
    A function that obtains the next job in the queue.

    Args:
        backend_name (str): The name of the backend

    Returns:
        the dict that contains the most important information about thejob
    """
    job_dict = {"job_id": 0, "job_json_path": "None"}

    job_json_dir = "/Backend_files/Queued_Jobs/" + backend_name + "/"

    job_list = self.get_file_queue(job_json_dir)

    # if there is a job, we should move it
    if job_list:
        job_json_name = job_list[0]
        job_dict["job_id"] = job_json_name[4:-5]

        # split the .json from the job_json_name
        job_json_name = job_json_name.split(".")[0]
        # and move the file into the right directory
        self.move_file(job_json_dir, "Backend_files/Running_Jobs", job_json_name)
        job_dict["job_json_path"] = "Backend_files/Running_Jobs"
    return job_dict


def modify_shot_output_folder(new_dir: str) -> None:
    """
    I am not sure what this function does.
    """
    defaut_shot_folder = str(remoteClient.get_shot_output_folder())
    modified_shot_folder = (defaut_shot_folder.rsplit("\\", 1)[0]) + "\\" + new_dir
    remoteClient.set_shot_output_folder(modified_shot_folder)


def add_job(json_dict: dict, status_msg_dict: dict) -> tuple[ResultDict, dict]:
    """
    The function that translates the json with the instructions into some circuit and executes it.
    It performs several checks for the job to see if it is properly working.
    If things are fine the job gets added the list of things that should be executed.

    json_dict: The job dictonary of all the instructions.
    status_msg_dict: the status dictionary of the job we are treating.
    """
    job_id = status_msg_dict["job_id"]

    result_dict: ResultDict = {
        "display_name": self.display_name,
        "backend_version": self.version,
        "job_id": job_id,
        "qobj_id": None,
        "success": True,
        "status": "finished",
        "header": {},
        "results": [],
    }
    err_msg, json_is_fine = self.check_json_dict(json_dict)
    if json_is_fine:
        # check_hilbert_space_dimension
        dim_err_msg, dim_ok = self.check_dimension(json_dict)
        if dim_ok:
            for exp in json_dict:
                exp_dict = {exp: json_dict[exp]}
                # Here we
                gen_script_and_globals(exp_dict, user_id)
                remoteClient.reset_shot_output_folder()
                modify_shot_output_folder(job_id + "\\" + str(exp))
                remoteClient.engage()  # check that this is blocking.

            status_msg_dict[
                "detail"
            ] += "; Passed json sanity check; Compilation done. Shots sent to solver."
            status_msg_dict["status"] = "DONE"
            return result_dict, status_msg_dict

        status_msg_dict["detail"] += (
            "; Failed dimensionality test. Too many atoms. File will be deleted. Error message : "
            + dim_err_msg
        )
        status_msg_dict["error_message"] += (
            "; Failed dimensionality test. Too many atoms. File will be deleted. Error message :  "
            + dim_err_msg
        )
        status_msg_dict["status"] = "ERROR"
        return result_dict, status_msg_dict
    else:
        status_msg_dict["detail"] += (
            "; Failed json sanity check. File will be deleted. Error message : "
            + err_msg
        )
        status_msg_dict["error_message"] += (
            "; Failed json sanity check. File will be deleted. Error message : "
            + err_msg
        )
        status_msg_dict["status"] = "ERROR"

    return result_dict, status_msg_dict


def gen_script_and_globals(json_dict, user_id) -> str:
    """
    This is the main script that generates the labscript file.

    In the sqooler project we call this the main function.
    """
    globals_dict = {
        "user_id": "guest",
        "shots": json_dict[next(iter(json_dict))]["shots"],
    }
    globals_dict["shots"] = 4
    globals_dict["user_id"] = user_id

    remoteClient.set_globals(globals_dict)
    remoteClient.set_globals(globals_dict)
    script_name = "Experiment_" + globals_dict["user_id"] + ".py"
    exp_script = os.path.join(EXP_SCRIPT_FOLDER, script_name)
    ins_list = json_dict[next(iter(json_dict))]["instructions"]
    func_dict = {
        "rLx": "rLx",
        "rLz2": "rLz2",
        "rLz": "rLz",
        "delay": "delay",
        "measure": "measure",
        "barrier": "barrier",
    }
    code = ""

    # pylint: disable=bare-except
    try:
        with open(HEADER_PATH, "r", encoding="UTF-8") as header_file:
            code = header_file.read()
    except:
        print("Something wrong. Does header file exists?")

    # pylint: disable=bare-except
    try:
        with open(exp_script, "w", encoding="UTF-8") as script_file:
            script_file.write(code)
    except:
        print("Something wrong. Does file path exists?")

    for inst in ins_list:
        func_name = func_dict[inst[0]]
        params = "(" + str(inst[1:])[1:-1] + ")"
        code = "Experiment." + func_name + params + "\n"

        # we should add proper error handling here
        # pylint: disable=bare-except
        try:
            with open(exp_script, "a", encoding="UTF-8") as script_file:
                script_file.write(code)
        except:
            print("Something wrong. Does file path exists?")

    code = "Experiment.final_action()" + "\n" + "stop(Experiment.t+0.1)"
    # pylint: disable=bare-except
    try:
        with open(exp_script, "a", encoding="UTF-8") as script_file:
            script_file.write(code)
    except:
        print("Something wrong. Does file path exists?")
    remoteClient.set_labscript_file(
        exp_script
    )  # CAUTION !! This command only selects the file. It does not generate it!
    return exp_script
