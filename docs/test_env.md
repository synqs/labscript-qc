# Test up a test env

How can we set up a test environment for the project?

1. Create a new virtual environment
2. Install labscript-suite `pip install labscript-suite`
3. Set up labscript-suite `labscript-profile-create`

## Set on mac

on a macbook the situation is a bit annoying

You have to activate conda and the x86 environment first

```bash
conda create -n labscript-qc-x86 -y
conda activate labscript-qc-x86
conda config --env --set subdir osx-64
```

Now install python 3.10

```bash
conda install python=3.10
```

Now we can continue with the normal steps described [here](https://docs.labscriptsuite.org/en/latest/installation/regular-anaconda/).

Then to start the test script you have to make sure that labscript-suite is properly running in another terminal.