BOSCO module
============
This repository contains the following files: 

bosco - directory containing installed BOSCO files 

connect-1.0 - modulefile for BOSCO

connect - Connect program

setup.sh - Connect extension that sets up BOSCO for the user

addsite.sh - Connect extension that adds another cluster to BOSCO for the user 

How to test
-----------
1. ssh into user@midway.rcc.uchicago.edu
2. cd privatemodules (try "module load use.own" if the directory does not exist)
3. module load git
4. git clone https://github.com/SISC2014/Bosco-Module.git
5. mv Bosco-Module connect
6. cp -r connect/bosco ~/bosco
7. mkdir -p ~/lib/connect/extensions
8. cp connect/setup.sh ~/lib/connect/extensions/setup.sh
9. module load use.own
10. module load connect
11. connect setup
12. enter your ssh user/password to UChicago Connect when prompted

Bosco should be set up, with the UChicago Connect cluster added. Run "condor_submit" to submit jobs (currently supports grid universe only) and "condor_q" to check jobs. 

User Guide 
----------
###Login to Midway

To begin, log in to the Research Computing Center's Midway cluster. If not already registered to Midway, go to the [RCC's website](http://rcc.uchicago.edu/) and sign up for an account there. Using the BOSCO module also requires an account on [RCC Connect](http://ci-connect.uchicago.edu/).

```
$ ssh username@midway.rcc.uchicago.edu
```

###Set up Connect and BOSCO

Once logged in to Midway, set up the Connect program with the following step:

```
$ module load connect
```

Now you will have access to all of the Connect program extensions. For a list of available extensions, enter the following command:

```
$ connect available
```

To run any of these extensions, just enter "connect <extension name>". For example, enter the command below to set up BOSCO: 

```
$ connect setup
```

The command will start BOSCO and ask for a username and password to access RCC Connect. Once the setup is over, you will be able to submit jobs via BOSCO to RCC Connect. 

###Tutorial jobs 

TODO: Look at OSG Connect Quickstart tutorial