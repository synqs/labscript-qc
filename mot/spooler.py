"""
This is the file that creates the labscript file and sends it to the BLACS.
"""
import os
from pprint import pprint
import runmanager.remote


remoteClient = runmanager.remote.Client()

# remote files
REMOTE_BASE_PATH = "."
RECEIVED_JSON_FOLDER = f"{REMOTE_BASE_PATH}"
EXECUTED_JSON_FOLDER = f"{REMOTE_BASE_PATH}/executed"
JSON_STATUS_FOLDER = f"{REMOTE_BASE_PATH}/status"


# in the labscript ini file this is equivalent to the the path `labscriptlib`
EXP_SCRIPT_FOLDER = "/Users/fredjendrzejewski/labscript-suite/userlib/labscriptlib/mot"
# local files
HEADER_PATH = f"{EXP_SCRIPT_FOLDER}/header.py"


def get_file_queue(dir_path: str) -> list:
    """
    A function that returns the list of files in the directory.
    """
    files = list(fn for fn in next(os.walk(dir_path))[2])
    return files


def modify_shot_output_folder(new_dir: str) -> None:
    """
    I am not sure what this function does.
    """
    defaut_shot_folder = str(remoteClient.get_shot_output_folder())
    modified_shot_folder = (defaut_shot_folder.rsplit("\\", 1)[0]) + "\\" + new_dir
    remoteClient.set_shot_output_folder(modified_shot_folder)


def gen_script_and_globals(json_dict: dict, job_id: str) -> str:
    """
    This is the main script that generates the labscript file.

    Args:
        json_dict: The dictionary that contains the instructions for the circuit.
        job_id: The user id of the user that is running the experiment.

    Returns:
        The path to the labscript file.
    """
    globals_dict = {
        "job_id": "guest",
        "shots": json_dict[next(iter(json_dict))]["shots"],
    }

    globals_dict["shots"] = 4
    globals_dict["job_id"] = job_id

    # TODO: this is currently hanging
    # let us simply comment it for the moment as we do not know what it does
    # anyways
    # remoteClient.set_globals(globals_dict)
    script_name = f"experiment_{globals_dict['job_id']}.py"
    exp_script = os.path.join(EXP_SCRIPT_FOLDER, script_name)
    ins_list = json_dict[next(iter(json_dict))]["instructions"]
    print(f"File path: {exp_script}")
    code = ""
    # this is the top part of the script it allows us to import the
    # typical functions that we require for each single sequence
    with open(HEADER_PATH, "r", encoding="UTF-8") as header_file:
        code = header_file.read()

    # add a line break to the code
    code += "\n"
    # pylint: disable=bare-except
    try:
        with open(exp_script, "w", encoding="UTF-8") as script_file:
            script_file.write(code)
    except:
        print("Something wrong. Does file path exists?")

    for inst in ins_list:
        # we can directly use the function name as we have already verified
        # that the function exists in the `add_job` function
        func_name = inst[0]
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
    print("Script generated.")
    return exp_script
