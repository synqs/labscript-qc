import time
from utils.storage_providers import MongodbProvider

from mot.spooler import add_job

storage_provider = MongodbProvider()

from mot.config import spooler_object as mot_spooler

# configure the backends
backends = {
    "mot": mot_spooler,
}


def update_backends() -> None:
    """
    Update the backends on the storage.
    """
    for requested_backend, spooler in backends.items():
        # the content
        backend_config_dict = spooler.get_configuration()
        # set the display name
        backend_config_dict["display_name"] = requested_backend

        # upload the content through the storage provider
        storage_provider.upload_config(backend_config_dict, requested_backend)


def main() -> None:
    """
    Function for processing jobs continuously.
    """
    backends_list = list(backends.keys())

    # set the appropiate display names for all the back-ends
    for requested_backend, spooler in backends.items():
        spooler.display_name = requested_backend

    while True:
        time.sleep(3)
        print("Run again")
        requested_backend = backends_list[0]
        backends_list.append(backends_list.pop(0))
        # I should most certainly make this fairly close to the logic in the `sqooler`
        # this is basically looking for the json file in the folder.

        job_dict = storage_provider.get_next_job_in_queue(requested_backend)
        if job_dict["job_json_path"] == "None":
            continue
        job_json_dict = storage_provider.get_job_content(
            storage_path=job_dict["job_json_path"], job_id=job_dict["job_id"]
        )
        # next is to get the job content
        result_dict = None
        status_msg_dict = {
            "job_id": job_dict["job_id"],
            "status": "None",
            "detail": "None",
            "error_message": "None",
        }

        result_dict, status_msg_dict = add_job(job_json_dict, status_msg_dict)
        storage_provider.update_in_database(
            result_dict, status_msg_dict, job_dict["job_id"], requested_backend
        )


if __name__ == "__main__":
    print("Update")
    update_backends()
    print("Now run the main spooler.")
    main()
