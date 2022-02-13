# Important
This project is just one part of the bigger framework [qlue][qlue_github]. Check out [qlue][qlue_github] for more details.
## The Spooler.py

After the post_job view dumps the JSON files on the hard disk they have to be processed further to execute experiments on the cold atom machine. Also dumping files on the hard disk acts as a job queue so we do not need to use any extra package to queue the jobs.

In order to run experiments on our cold atom setup, we use the [labscript suite][labscript_github]. This means we have to convert the received JSONs into python code understandable by labscript. This is done by Spooler.py file. We will mention three parts of the labscript suite : **Runmanager**, **BLACS** and **Lyse**. Documentation about them is available at [labscript suite][labscript_github] repositories.

The Spooler checks for a job_JSON every 3 seconds in the dump location on the hard drive. It then picks up the job_JSON that was created first and starts to process it. After all the steps of processing are done the job_JSON file is moved to a different folder.

During processing, the spooler first checks if the JSON satisfies the schema. This is also a safety check which allows to see if the user submitted anything in the JSON which is inappropriate. After this it updates the status dictionary. Then it continues processing by using the JSON to extract an experiment python file for labscript and set the value of parameters in **Runmanager**. After generating the files and setting parameters, the spooler triggers the execution of the experiment via runmanger remote API commands. The status dictionary for that job is appropriately updated.

In labscript all the shots generated from a given python code are stored as HDF files. Lets say for a given experiment python file we have 10 shots i.e. 10 HDF files. These shots are passed from **Runmanager** to **BLACS** for actual execution. **BLACS** queues all the shots and executes them sequentially. All data pertaining to a shot (e.g. value of parameters, camera images etc.) is stored in its HDF file. Further data analysis is now run on these HDF files.

## The Result.py
After the shots have been executed, we use **Lyse** to run analysis routines on the HDF files. There are two types of analysis routines: single shot and multi shot. Single shot routines are run on each shot individually for e.g. calculate atom number in each shot or size of atom cloud in each shot. Multishot routines are run on a collection of shots and are helpful to see for e.g. how the atom number in each shot changed as some parameter was varied across shots.

Given the location of a shot folder **Lyse** can generate a pandas dataframe by reading all the values, be it **Runmanager** globals or analysis routine results. It is this pandas dataframe we are interested in.

Currently by using QisKit plugin if we had to scan a parameter across shots, it was done by creating a new experiment dictionary for each value of the parameter. So for e.g. if we want to scan a parameter across 5 values, our job_JSON dictionary will have 5 nested experiment dictionaries in it, one each for a particular value of the parameter. And each of the 5 experiment dictionaries will also have a **shots** key which will tell how many times that particular experiment is repeated.

When the Spooler starts execution of this JSON in labscript, it will create a job folder with job_id name. Inside this job folder there will be 5 sub-folders one for each experiment. Inside each experiment's folder will be the HDF files for the shots of that particular experiment.

As the individual shots get executed they dump their complete HDF path in a separate text file (call it address_file) for each shot. This way we know which shots have finished executing. The result.py keeps checking this dump location for these address_files and selects the first created address_file. It gets the shot path in it and starts with processing of that particular shot. First it will run all single shot analysis routines on this files as defined in the **store_result()** function. The results of the single shot analysis are stored inside the HDF file by creating appropriate groups. After this it calls the  **move_to_sds()** function which will move the HDF file from this location to a network storage i.e. SDS. Also it will move the address_file of this shot from the original dump location to a new one.

After moving to SDS, the result.py updates a job_dictionary which is initially read from a text file. This dictionary keeps track of all running jobs. If the job_id of the shot just moved to SDS is not in this dictionary, it is included along-with its folder location in SDS. This dictionary is also useful to determine on which job a multi-shot analysis can be run. The result.py checks the first key in this dictionary and figures out if that job is done or not. If yes then it proceeds with multi-shot analysis for that job by using **Lyse** to generate CSV from pandas dataframe for each sub-folder of the experiments in a job. After generating CSVs it generates the result JSON for this job in a specific format given by the schema we decided in [1][eggerdj_github]. Then it updates the status of this job to 'DONE'. Finally the finished job is removed from the dictionary of running jobs.


[qlue_github]: https://github.com/synqs/qlue "qlue"
[eggerdj_github]: https://github.com/eggerdj/backends/ "Qiskit_json"
[labscript_github]: https://github.com/labscript-suite "labscript"