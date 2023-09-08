"""
Test module for the mot file.
"""

from typing import Union
import numpy as np

import pytest
from pydantic import ValidationError


from mot.config import (
    spooler_object as spooler,
    MotExperiment,
    MeasureBarrierInstruction,
    LoadInstruction,
)

from utils.schemes import gate_dict_from_list, ResultDict


def run_json_circuit(json_dict: dict, job_id: Union[int, str]) -> ResultDict:
    """
    A support function that executes the job.

    Args:
        json_dict: the job dict that will be treated
        job_id: the number of the job

    Returns:
        the results dict
    """
    status_msg_dict = {
        "job_id": job_id,
        "status": "None",
        "detail": "None",
        "error_message": "None",
    }

    result_dict, status_msg_dict = spooler.add_job(json_dict, status_msg_dict)
    assert status_msg_dict["status"] == "DONE", "Job failed"
    return result_dict


def test_pydantic_exp_validation() -> None:
    """
    Test that the validation of the experiment is working
    """
    experiment = {
        "instructions": [
            ["load", [7], []],
            ["load", [2], []],
            ["measure", [2], []],
            ["measure", [6], []],
            ["measure", [7], []],
        ],
        "num_wires": 1,
        "shots": 4,
        "wire_order": "interleaved",
    }
    MotExperiment(**experiment)

    with pytest.raises(ValidationError):
        poor_experiment = {
            "instructions": [
                ["load", [7], []],
                ["load", [2], []],
                ["measure", [2], []],
                ["measure", [6], []],
                ["measure", [7], []],
            ],
            "num_wires": 8,
            "shots": 4,
            "wire_order": "sequential",
        }
        MotExperiment(**poor_experiment)


def test_barrier_instruction() -> None:
    """
    Test that the barrier instruction is properly constrained.
    """
    inst_list = ["barrier", [0], []]
    gate_dict = gate_dict_from_list(inst_list)
    assert gate_dict == {
        "name": inst_list[0],
        "wires": inst_list[1],
        "params": inst_list[2],
    }
    MeasureBarrierInstruction(**gate_dict)
    # test that the name is nicely fixed
    with pytest.raises(ValidationError):
        poor_inst_list = ["barriers", [7], []]
        gate_dict = gate_dict_from_list(poor_inst_list)
        MeasureBarrierInstruction(**gate_dict)

    # test that we cannot give too many wires
    with pytest.raises(ValidationError):
        poor_inst_list = ["barrier", [0, 1, 2, 3, 4, 5, 6, 7, 8], []]
        gate_dict = gate_dict_from_list(poor_inst_list)
        MeasureBarrierInstruction(**gate_dict)

    # make sure that the wires cannot be above the limit
    with pytest.raises(ValidationError):
        poor_inst_list = ["barrier", [8], []]
        gate_dict = gate_dict_from_list(poor_inst_list)
        MeasureBarrierInstruction(**gate_dict)

    # make sure that the parameters are enforced to be empty
    with pytest.raises(ValidationError):
        poor_inst_list = ["barrier", [7], [2.3]]
        gate_dict = gate_dict_from_list(poor_inst_list)
        MeasureBarrierInstruction(**gate_dict)


def test_load_measure_instruction() -> None:
    """
    Test that the barrier instruction is properly constrained.
    """
    inst_list = ["load", [0], [2]]
    gate_dict = gate_dict_from_list(inst_list)
    assert gate_dict == {
        "name": inst_list[0],
        "wires": inst_list[1],
        "params": inst_list[2],
    }
    LoadInstruction(**gate_dict)

    inst_list = ["measure", [0], []]
    gate_dict = gate_dict_from_list(inst_list)
    assert gate_dict == {
        "name": inst_list[0],
        "wires": inst_list[1],
        "params": inst_list[2],
    }
    MeasureBarrierInstruction(**gate_dict)

    # test that the name is nicely fixed
    with pytest.raises(ValidationError):
        poor_inst_list = ["loads", [0], []]
        gate_dict = gate_dict_from_list(poor_inst_list)
        LoadInstruction(**gate_dict)

    # test that we cannot give too many wires
    with pytest.raises(ValidationError):
        poor_inst_list = ["load", [0, 1], [2]]
        gate_dict = gate_dict_from_list(poor_inst_list)
        LoadInstruction(**gate_dict)

    # make sure that the wires cannot be above the limit
    with pytest.raises(ValidationError):
        poor_inst_list = ["load", [2], [3]]
        gate_dict = gate_dict_from_list(poor_inst_list)
        LoadInstruction(**gate_dict)

    # make sure that the parameters are enforced to be empty
    with pytest.raises(ValidationError):
        poor_inst_list = ["measure", [0], [2.3]]
        gate_dict = gate_dict_from_list(poor_inst_list)
        LoadInstruction(**gate_dict)


def test_load_gate() -> None:
    """
    Test that the loading is properly working.
    """

    # first submit the job
    job_payload = {
        "experiment_0": {
            "instructions": [
                ["load", [0], [20]],
                ["measure", [0], []],
            ],
            "num_wires": 1,
            "shots": 4,
            "wire_order": "interleaved",
        },
    }

    job_id = "1"
    data = run_json_circuit(job_payload, job_id)

    shots_array = data["results"][0]["data"]["memory"]
    assert data["job_id"] == job_id, "job_id got messed up"
    assert len(shots_array) > 0, "shots_array got messed up"
    assert shots_array[0] == "1 0 1", "shots_array got messed up"


def test_number_experiments() -> None:
    """
    Make sure that we cannot submit too many experiments.
    """

    # first test the system that is fine.
    job_payload = {
        "experiment_0": {
            "instructions": [
                ["load", [0], [50]],
                ["measure", [0], []],
            ],
            "num_wires": 1,
            "shots": 4,
            "wire_order": "interleaved",
        },
    }
    job_id = 1
    data = run_json_circuit(job_payload, job_id)

    shots_array = data["results"][0]["data"]["memory"]
    assert len(shots_array) > 0, "shots_array got messed up"
    inst_dict = {
        "instructions": [
            ["load", [0], [50]],
            ["measure", [0], []],
        ],
        "num_wires": 1,
        "shots": 4,
        "wire_order": "interleaved",
    }

    # and now run too many experiments
    n_exp = 2000
    job_payload = {}
    for ii in range(n_exp):
        job_payload[f"experiment_{ii}"] = inst_dict
    job_id = 1
    with pytest.raises(AssertionError):
        data = run_json_circuit(job_payload, job_id)


def test_seed() -> None:
    """
    Test that the hopping is properly working.
    """

    # first submit the job
    job_payload = {
        "experiment_0": {
            "instructions": [
                ["load", [0], []],
                ["load", [1], []],
                ["fhop", [0, 4, 1, 5], [np.pi / 4]],
                ["measure", [0], []],
                ["measure", [1], []],
                ["measure", [4], []],
                ["measure", [5], []],
            ],
            "num_wires": 8,
            "shots": 4,
            "wire_order": "interleaved",
            "seed": 12345,
        },
        "experiment_1": {
            "instructions": [
                ["load", [0], []],
                ["load", [1], []],
                ["fhop", [0, 4, 1, 5], [np.pi / 4]],
                ["measure", [0], []],
                ["measure", [1], []],
                ["measure", [4], []],
                ["measure", [5], []],
            ],
            "num_wires": 8,
            "shots": 4,
            "wire_order": "interleaved",
            "seed": 12345,
        },
    }

    job_id = "1"
    data = run_json_circuit(job_payload, job_id)

    shots_array_1 = data["results"][0]["data"]["memory"]
    shots_array_2 = data["results"][1]["data"]["memory"]
    assert data["job_id"] == job_id, "job_id got messed up"
    assert len(shots_array_1) > 0, "shots_array got messed up"
    assert shots_array_1 == shots_array_2, "seed got messed up"


def test_spooler_config() -> None:
    """
    Test that the back-end is properly configured and we can indeed provide those parameters
     as we would like.
    """
    fermion_config_dict = {
        "description": (
            "simulator of a fermionic tweezer hardware. "
            "The even wires denote the occupations of the spin-up fermions"
            " and the odd wires denote the spin-down fermions"
        ),
        "version": "0.1",
        "cold_atom_type": "fermion",
        "gates": [
            {
                "coupling_map": [
                    [0, 1, 2, 3],
                    [2, 3, 4, 5],
                    [4, 5, 6, 7],
                    [0, 1, 2, 3, 4, 5, 6, 7],
                ],
                "description": "hopping of atoms to neighboring tweezers",
                "name": "fhop",
                "parameters": ["j_i"],
                "qasm_def": "{}",
            },
            {
                "coupling_map": [[0, 1, 2, 3, 4, 5, 6, 7]],
                "description": "on-site interaction of atoms of opposite spin state",
                "name": "fint",
                "parameters": ["u"],
                "qasm_def": "{}",
            },
            {
                "coupling_map": [
                    [0, 1],
                    [2, 3],
                    [4, 5],
                    [6, 7],
                    [0, 1, 2, 3, 4, 5, 6, 7],
                ],
                "description": "Applying a local phase to tweezers through an external potential",
                "name": "fphase",
                "parameters": ["mu_i"],
                "qasm_def": "{}",
            },
        ],
        "max_experiments": 1000,
        "max_shots": 1000000,
        "simulator": True,
        "supported_instructions": [
            "load",
            "barrier",
            "fhop",
            "fint",
            "fphase",
            "measure",
        ],
        "num_wires": 8,
        "wire_order": "interleaved",
        "num_species": 2,
    }
    spooler_config_dict = spooler.get_configuration()
    assert spooler_config_dict == fermion_config_dict


def test_add_job() -> None:
    """
    Test if we can simply add jobs as we should be able too.
    """

    # first test the system that is fine.
    job_payload = {
        "experiment_0": {
            "instructions": [
                ["load", [0], []],
                ["fhop", [0, 4, 1, 5], [np.pi / 4]],
                ["fphase", [2, 6], [np.pi]],
                ["fhop", [0, 4, 1, 5], [np.pi / 4]],
                ["measure", [0], []],
                ["measure", [1], []],
            ],
            "num_wires": 8,
            "shots": 2,
            "wire_order": "interleaved",
        },
    }

    job_id = 1
    status_msg_dict = {
        "job_id": job_id,
        "status": "None",
        "detail": "None",
        "error_message": "None",
    }
    result_dict, status_msg_dict = spooler.add_job(job_payload, status_msg_dict)
    # assert that all the elements in the result dict memory are of string '1 0'
    expected_value = "0 1"
    for element in result_dict["results"][0]["data"]["memory"]:
        assert (
            element == expected_value
        ), f"Element {element} is not equal to {expected_value}"
