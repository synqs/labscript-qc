"""
The module treats the result of the experiment and formats them appropriately for the user. 
Only after the data treatment is done the status of the job is changed to done.
So this is basically the last step of the sqooler.
"""
#!/usr/bin/env python
# coding: utf-8

import json
import os
import time
import shutil

import numpy as np
import numpy.typing as npt

from lyse import dataframe_utilities
import pandas as pd
import h5py


def get_spin_up_down_atoms(
    atom_image: npt.ArrayLike, ref_image: npt.ArrayLike, dark_image: npt.ArrayLike
) -> tuple[np.ndarray, np.ndarray]:
    """
    No idea what this function does. I would guess that it can be use for Stern-Gerlach
    analysis.
    """
    # pylint: disable=unused-argument
    atoms_per_site = np.arange(1e4, 4e4, 1e4)
    return atoms_per_site, 0.1 * atoms_per_site


def store_result(shot_path) -> None:
    """
    No idea what this function does.
    """
    with h5py.File(shot_path, "r+") as file:
        atom_image = np.identity(10)
        ref_image = np.identity(10)
        dark_image = np.identity(10)
        spin_up, spin_down = get_spin_up_down_atoms(atom_image, ref_image, dark_image)

        # one day we should narrow the exception
        # pylint: disable=bare-except
        try:
            analyis_results_group = file.create_group("results/Atom_occup")
        except:
            analyis_results_group = file["results/Atom_occup"]
        for i in range(spin_up.size):
            site = str(i)
            atom_num_arr = np.array((spin_up[i], spin_down[i]))
            analyis_results_group.attrs.create(
                "Wire_" + site, data=atom_num_arr, shape=np.shape(atom_num_arr)
            )


def move_to_sds(shot_path, running_file_path, finished_file_path):
    """
    No idea what this function does.
    """
    dst_path = str("D") + shot_path[1:]
    dst_dir = dst_path.rpartition("\\")[0]
    os.makedirs(dst_dir, exist_ok=True)
    shutil.move(shot_path, dst_path)
    shutil.move(running_file_path, finished_file_path)
    return dst_path


def check_job_done(selected_job_id, job_folder_for_csv) -> bool:
    """
    No idea what this function does.
    """

    # why is the job_id not used ?
    # pylint: disable=unused-argument
    original_job_folder = "C" + job_folder_for_csv[1:]
    last_sub_folder = sorted(os.listdir(original_job_folder))[
        -1
    ]  # next(os.walk(job_folder_for_csv))[1][-1]
    last_sub_folder_path = os.path.join(original_job_folder, last_sub_folder)
    num_remaining_shots = len(
        os.listdir(last_sub_folder_path)
    )  # len(next(os.walk(last_sub_folder_path))[2])
    job_done = False
    if not num_remaining_shots:
        job_done = True
    return job_done


def gen_multishot_csvs(job_folder_for_csv):
    """
    No idea what this function does.
    """
    subfolder_list = next(os.walk(job_folder_for_csv))[1]
    shot_subfolder_paths = [
        os.path.join(job_folder_for_csv, fn) for fn in subfolder_list
    ]
    for i in range(len(shot_subfolder_paths)):
        file_list = list(fn for fn in next(os.walk(shot_subfolder_paths[i]))[2])
        shot_paths = [os.path.join(shot_subfolder_paths[i], fn) for fn in file_list]
        df = dataframe_utilities.get_dataframe_from_shots(shot_paths)
        df.columns = ["_".join(tup).rstrip("_") for tup in df.columns.values]
        path_csv = os.path.join(job_folder_for_csv, "df_" + subfolder_list[i] + ".csv")
        df.to_csv(path_csv, index=False)


def create_memory_data(data_frame, name):
    """
    No idea what this function does.
    """
    exp_sub_dict = {
        "header": {"name": "experiment_0", "extra metadata": "text"},
        "shots": 3,
        "success": True,
        "data": {"memory": None},  # slot 1 (Na)      # slot 2 (Li)
    }
    exp_sub_dict["header"]["name"] = name
    exp_sub_dict["shots"] = data_frame.shape[0]
    memory_df = data_frame.loc[:, data_frame.columns.str.startswith("Atom_occup_Wire")]

    # no idea what will happen in this code
    l_var = list(memory_df.astype(str).values.sum(axis=1))
    memory_list = [
        w.replace("][", " ; ").replace(",", "").replace("[", "").replace("]", "")
        for w in l_var
    ]
    exp_sub_dict["data"]["memory"] = memory_list
    return exp_sub_dict


def create_json_result(selected_job_id, job_folder_for_csv) -> dict:
    """
    I think this function creates the json file that is sent to the user.

    So the result_dict should be most likely as in the sqooler.
    """
    result_dict = {
        "backend_name": "SoPa_atomic_mixtures",
        "backend_version": "0.0.1",
        "job_id": "None",
        "qobj_id": None,
        "success": True,
        "status": "finished",
        "header": {},
        "results": [],
    }
    result_dict["job_id"] = selected_job_id
    exp_list = next(os.walk(job_folder_for_csv))[1]

    for exp in exp_list:
        path_csv = os.path.join(job_folder_for_csv, "df_" + exp + ".csv")
        df = pd.read_csv(path_csv)
        result_dict["results"].append(create_memory_data(df, exp))
    return result_dict


def change_json_status_to_done(json_status_folder, selected_job_id) -> None:
    """
    This is most certainly the function that changes the status of the job to done.
    """
    status_file_name = "status_" + selected_job_id + ".json"
    status_file_path = os.path.join(json_status_folder, status_file_name)
    status_msg_dict = {"job_id": "None", "status": "None", "detail": "None"}
    with open(status_file_path, encoding="utf-8") as status_file:
        status_msg_dict = json.load(status_file)
    status_msg_dict["detail"] += "; BLACS and analysis done. Results are available!"
    status_msg_dict["status"] = "DONE"
    with open(status_file_path, "w", encoding="utf-8") as status_file:
        json.dump(status_msg_dict, status_file)


def do_analysis() -> None:
    """
    The main function of the module. It is running until someone stops it.
    """
    job_dict_file = R"C:\Experiments\Job_management\Running\multi_analysis_dict.json"
    running_folder = R"C:\Experiments\Job_management\Running"
    finished_folder = R"C:\Experiments\Job_management\Finished"
    result_json_folder = R"Y:\uploads\results"
    json_status_folder = R"Y:\uploads\status"
    keep_analysing_file = R"C:\Experiments\Job_management\keep_analysing.txt"
    while True:
        time.sleep(2)
        if not os.path.isfile(keep_analysing_file):
            print("You must create a keep_analysing file")
            break

        with open(job_dict_file, "r", encoding="utf-8") as file:
            job_dict = json.load(file)

        job_id_list = list(job_dict.keys())
        file_name = list(
            fn
            for fn in next(os.walk(running_folder))[2]
            if fn != "multi_analysis_dict.json"
        )  # sort this list
        if file_name:
            file_name = sorted(file_name)[0]
            running_file_path = os.path.join(running_folder, file_name)
            finished_file_path = os.path.join(finished_folder, file_name)
            with open(running_file_path, "r", encoding="utf-8") as text_file:
                shot_path = text_file.read()

            store_result(shot_path)
            shot_path = move_to_sds(shot_path, running_file_path, finished_file_path)

            current_job_id = file_name.split("-")[0]
            current_job_id_folder = os.path.join(
                shot_path.split(current_job_id)[0], current_job_id
            )

            if not current_job_id in job_id_list:
                job_dict[current_job_id] = current_job_id_folder

        job_id_list = list(job_dict.keys())
        job_done = False
        if job_id_list:
            selected_job_id = job_id_list[0]
            job_folder_for_csv = job_dict[selected_job_id]
            job_done = check_job_done(selected_job_id, job_folder_for_csv)
        if job_done:
            gen_multishot_csvs(job_folder_for_csv)
            result_dict = create_json_result(selected_job_id, job_folder_for_csv)
            result_json_path = os.path.join(
                result_json_folder, "result_" + selected_job_id + ".json"
            )
            with open(result_json_path, "w", encoding="utf-8") as file:
                json.dump(result_dict, file)
            change_json_status_to_done(json_status_folder, selected_job_id)
            del job_dict[selected_job_id]

        with open(job_dict_file, "w", encoding="utf-8") as file:
            json.dump(job_dict, file)


if __name__ == "__main__":
    print("Now run the analysis.")
    do_analysis()
