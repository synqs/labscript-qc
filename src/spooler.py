"""
This is the file that creates the labscript file and sends it to the BLACS.
"""
import json
import os
import time
import shutil

import runmanager.remote
from jsonschema import validate

remoteClient = runmanager.remote.Client()
RECEIVED_JSON_FOLDER = R"Y:\uploads"
EXECUTED_JSON_FOLDER = R"Y:\uploads\executed"
JSON_STATUS_FOLDER = R"Y:\uploads\status"
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
    This function checks if the json file is valid.
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


def modify_shot_output_folder(new_dir: str) -> None:
    """
    I am not sure what this function does.
    """
    defaut_shot_folder = str(remoteClient.get_shot_output_folder())
    modified_shot_folder = (defaut_shot_folder.rsplit("\\", 1)[0]) + "\\" + new_dir
    remoteClient.set_shot_output_folder(modified_shot_folder)


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


def main() -> None:
    """
    Function for processing jobs continuously.
    """
    while True:
        time.sleep(3)
        files = list(fn for fn in next(os.walk(RECEIVED_JSON_FOLDER))[2])
        if not files:
            continue

        json_name = (sorted(files))[0]
        ji_ui = (json_name)[5:-5]
        job_id, user_id = ji_ui.split("-")
        recieved_json_path = os.path.join(RECEIVED_JSON_FOLDER, json_name)
        executed_json_path = os.path.join(EXECUTED_JSON_FOLDER, json_name)
        status_file_name = "status_" + job_id + ".json"
        status_file_path = os.path.join(JSON_STATUS_FOLDER, status_file_name)
        status_msg_dict = {"job_id": "None", "status": "None", "detail": "None"}
        with open(recieved_json_path, encoding="UTF-8") as file:
            data = json.load(file)
            err_msg, json_is_fine = check_json_dict(data)
        if json_is_fine:
            with open(status_file_path, encoding="UTF-8") as status_file:
                status_msg_dict = json.load(status_file)
                status_msg_dict["detail"] += "; Passed json sanity check"
            with open(status_file_path, "w", encoding="UTF-8") as status_file:
                json.dump(status_msg_dict, status_file)
            for exp in data:
                exp_dict = {exp: data[exp]}
                gen_script_and_globals(exp_dict, user_id)
                remoteClient.reset_shot_output_folder()
                modify_shot_output_folder(job_id + "\\" + str(exp))
                remoteClient.engage()  # check that this is blocking.
            with open(status_file_path, encoding="UTF-8") as status_file:
                status_msg_dict = json.load(status_file)
                status_msg_dict["detail"] += "; Compilation done. Shots sent to BLACS"
                status_msg_dict["status"] = "RUNNING"
            with open(status_file_path, "w", encoding="UTF-8") as status_file:
                json.dump(status_msg_dict, status_file)
            shutil.move(recieved_json_path, executed_json_path)
            # os.remove(recieved_json_path)
            # os.remove(exp_script)
        else:
            with open(status_file_path, encoding="UTF-8") as status_file:
                status_msg_dict = json.load(status_file)
                status_msg_dict["detail"] += (
                    "; Failed json sanity check. File will be deleted. Error message : "
                    + err_msg
                )
                status_msg_dict["status"] = "ERROR"
            with open(status_file_path, "w", encoding="UTF-8") as status_file:
                json.dump(status_msg_dict, status_file)
            os.remove(recieved_json_path)


if __name__ == "__main__":
    print("Now run the main spooler.")
    main()
