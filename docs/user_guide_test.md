# Django for labscript

## The big picture
There are two sides : server and client. A client is a remote user who will write quantum circuits in the user's favorite framework (Qiskit/Pennylane). These circuits then have to be compiled into JSON files. The JSON files can be sent over the internet to a remote server which will try to parse them into meaningful instructions for the backend. The backend can be a real cold atom machine or just a simulator running on a computer. hihh [1][eggerdj_github].
![](big_pic.png)

## Components of the server

### The Django app

We describe the Django app which controls the communication to the real machine, but for other apps, the views and their purpose are similar. Django is a Python-based free and open-source web framework. It uses the Model-View-Template architecture:


### The Spooler.py
After the post_job view dumps the JSON files on the hard disk they have to be processed further to execute experiments on the cold atom machine. Also dumping files on the hard disk acts as a job queue so we do not need to use any extra package to queue the jobs.


### The Result.py
After the shots have been executed, we use **Lyse** to run analysis routines on the HDF files. There are two types of analysis routines: single shot and multi shot. Single shot routines are run on each shot individually for e.g. calculate atom number in each shot or size of atom cloud in each shot. Multishot routines are run on a collection of shots and are helpful to see for e.g. how the atom number in each shot changed as some parameter was varied across shots.

## Using SSH tunneling to reach the server
For enabling the remote client to talk to the server we need to setup a secure communication link. For this we use SSH tunneling as shown e

[eggerdj_github]: https://github.com/eggerdj/backends/ "Qiskit_json"
