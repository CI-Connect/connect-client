Connect Client 
==============
  * [Connect Client ](#connect-client-)
    * [Introduction](#introduction)
      * [Contact us](#contact-us)
    * [Installation](#installation)
      * [Obtaining the Connect Client distribution](#obtaining-the-connect-client-distribution)
      * [Installation by an individual user](#installation-by-an-individual-user)
      * [Installation by a site administrator](#installation-by-a-site-administrator)
    * [Setting up Connect Client](#setting-up-connect-client)
      * [Using environment modules](#using-environment-modules)
      * [Without environment modules](#without-environment-modules)
      * [Other](#other)
      * [First-time setup](#first-time-setup)
    * [Updating](#updating)
    * [User Guide](#user-guide)
      * [Connect Client commands](#connect-client-commands)
      * [Example submission](#example-submission)
        * [Create the HTCondor submit description file](#create-the-htcondor-submit-description-file)
        * [Submit the script](#submit-the-script)
        * [Check job queue](#check-job-queue)
        * [Job history](#job-history)
        * [Retrieve outputs](#retrieve-outputs)
        * [Check the job output](#check-the-job-output)
    * [Getting Help](#getting-help)

## Introduction

Connect Client is the set of programs and files for linking a campus
research computing cluster to a [CI Connect] instance (such as [OSG Connect])
which uses [HTCondor] to submit jobs to the [Open Science Grid].  The 
example below assumes one has already [signed up for an account] on OSG Connect.  If you don't have 
an account on OSG Connect, [apply now](https://confluence.grid.iu.edu/display/CON/Registration+and+login+instructions). 

### Contact us

For help or questions please email connect-support@opensciencegrid.org.


## Installation

Connect Client can be installed by an individual user or by an HPC site
administrator for system-wide usage.


### Obtaining the Connect Client distribution

Regardless of whether you are a user or an admin, the first step is the same:

    $ ssh login.mycluster.edu            # [your cluster site here]
    $ module load git                    # [if needed]
    $ git clone --recursive https://github.com/CI-Connect/connect-client

This obtains a copy of the distribution and sets your shell's working
directory to that copy. *The --recursive option is important!*

To install the Connect Client you will need Python 2.x and a C compiler.
*Python 3 is not supported.* At some sites, `module load python` will load
Python 3, so it _might_ be necessary to load Python 2 explicitly. For example:

    $ module load gcc
    $ module load python/2.7.6


### Installation by an individual user

Choose a directory to install Connect Client into.  A reasonable
choice is `~/software/connect`.  Also choose a directory for the
module description information.  A reasonable choice for this is
`~/privatemodules`; for many sites, this is where the `use.own`
module looks for personal modules.

Then run `./install.sh` with these two directories and a version
number (e.g. 0.3.0):

    $ cd connect-client
    $ ./install.sh ~/software/connect-client ~/privatemodules 0.3.0


### Installation by a site administrator

Typically this would be quite similar, only system paths would be used.
For example:

    $ cd connect-client
    $ ./install.sh -site /software/connect-client /software/modulefiles 0.3.0

Note the `-site` option.


N.B. Any modules that you have loaded at the time you install Connect
Client will be loaded by the Connect Client modulefile _each time you
load the `connect-client` module_. This ensures that dependencies are
handled internally. To reduce unnecessary module loads, be sure not to
load unnecessary modules before installing.


## Setting up Connect Client

### Using environment modules

To make Connect Client available, use the `module` command as you would
any other software module.  

    $ module load connect-client

For user installations with `module`, you'll need to load the `use.own` module first:

    $ module load use.own
    $ module load connect-client


### Without environment modules

If your site does not have environment modules, install the package as above and modify the $PATH:

    $ export PATH=~/software/connect-client/bin:$PATH


### Other

We expect to provide an RPM-based installation in the near future.


### First-time setup

Each user must perform this setup step once before using Connect Client
for the first time.  

    $ connect setup
    <enter your OSG Connect username and password when prompted>

The Connect Client should be set up, with the OSG Connect site
added. Test the setup with:

    $ connect test


## Updating

To update your connect client installation, it's necessary to re-install.
There are two paths. You can update using git:

    $ git pull
    $ ./install.sh ~/software/connect-client ~/privatemodules 0.3.0

Alternatively, you can delete your installation directory and restart
these instructions from the beginning.

If you need to revoke your access to the Connect server, either permanently
or for testing purposes:

    $ connect revoke


## User Guide 

### Connect Client commands

For a list of available commands, enter `connect` from the command line:
```
$ connect 
This is Connect Client v0.3-1-g59c218.
usage: connect [opts] <subcommand> [args]
       connect [opts] dag <dagfile>
       connect [opts] history <condor_history arguments>
       connect [opts] list [-v]
       connect [opts] modules 
       connect [opts] pull [-v|--verbose] [-w|--where] [repository-dir]
       connect [opts] push [-v|--verbose] [-w|--where] [repository-dir]
       connect [opts] q <condor_q arguments>
       connect [opts] revoke 
       connect [opts] rm <condor_rm arguments>
       connect [opts] run <condor_run arguments>
       connect [opts] setup [--replace-keys] [--update-keys] [servername]
       connect [opts] shell [command]
       connect [opts] status <condor_status arguments>
       connect [opts] submit <submitfile>
       connect [opts] sync [-v|--verbose] [-w|--where] [repository-dir]
       connect [opts] test  
       connect [opts] wait <condor_wait arguments>

opts:
    -s|--server hostname       set connect server name
    -u|--user username         set connect server user name
    -r|--remote directory      set connect server directory name
    -v|--verbose               show additional information
```

To run any of these commands, just enter `connect [opts] [command name]`.


### Example submission

Now let's create a test script for execution of 10 jobs on the OSG.
**Create a working directory (and logfile subdirectory)** that will be
synched with the remote host on the OSG Connect server.  

	$ cd
	$ tutorial quickstart
	Installing quickstart (osg)...
	Tutorial files installed in ./tutorial-quickstart.
	Running setup in ./tutorial-quickstart...
	$ cd tutorial-quickstart
	$ cat short.sh

Here is the short.sh script:

	#!/bin/bash
	# short.sh: a short discovery job 
	
	printf "Start time: "; /bin/date 
	printf "Job is running on node: "; /bin/hostname 
	printf "Job running as user: "; /usr/bin/id 
	printf "Job is running in directory: "; /bin/pwd 
	
	echo
	echo "Working hard..."
	sleep ${1-15}
	echo "Science complete!"

Make the script executable.

	$ chmod +x short.sh


#### Create the HTCondor submit description file

This tutorial is part of the greater [ConnectBook], which has many
illustrations of distributed computation jobs. We'll sample just one
here to show how to execute tutorials using Connect Client.

The `tutorial02.submit` file is a good foundation. Let's edit it, changing
it from 25 jobs to just 10:

	$ nano tutorial.submit

The submit file should contain the following:

	Universe = vanilla 

	Executable = short.sh 

	Error = log/job.error.$(Cluster)-$(Process) 
	Output = log/job.output.$(Cluster)-$(Process) 
	Log = log/job.log.$(Cluster) 

	Queue 25

Change `Queue 25` to `Queue 10`. This will create 10 instances of your
`short.sh` job.

In an HTCondor submit file, `$(Cluster)` labels the submission task
(called "Cluster ID") and `$(Process)` labels individual jobs in the
task. This submit file thus directs logs for each job into files in the
`log/` directory. You'll see the relevance of this further on.

#### Submit the script

Submit the script using `connect client submit tutorial02.submit`.  You
must invoke connect client commands from the working directory.

	$ connect client submit tutorial02.submit
	notice: sending README.md as tutorial-quickstart/README.md...
	notice: sending short.sh as tutorial-quickstart/short.sh...
	notice: sending tutorial01.submit as tutorial-quickstart/tutorial01.submit...
	notice: sending tutorial02.submit as tutorial-quickstart/tutorial02.submit...
	notice: sending tutorial03.submit as tutorial-quickstart/tutorial03.submit...
	notice: sending log/.gitignore as tutorial-quickstart/log/.gitignore...
	Submitting job(s).
	10 job(s) submitted to cluster 1234.

The `notice` lines indicate that files local to your client were transferred to the
server in order to submit the job.

**N.B. If your OSG Connect username differs from your local username,
set `CONNECT_CLIENT_USER` in your environment.**

	$ export CONNECT_CLIENT_USER=osgconnect-username
	$ connect client submit tutorial02.submit
	notice: sending README.md as tutorial-quickstart/README.md...
	notice: sending short.sh as tutorial-quickstart/short.sh...
	notice: sending tutorial01.submit as tutorial-quickstart/tutorial01.submit...
	notice: sending tutorial02.submit as tutorial-quickstart/tutorial02.submit...
	notice: sending tutorial03.submit as tutorial-quickstart/tutorial03.submit...
	notice: sending log/.gitignore as tutorial-quickstart/log/.gitignore...
	Submitting job(s).
	10 job(s) submitted to cluster 1234.


#### Check job queue
The **connect client q** command tells the status of submitted jobs:

	$ connect client q <osgconnect-username>

	-- Submitter: login01.osgconnect.net : <192.170.227.195:40814> : login01.osgconnect.net
 	ID      OWNER            SUBMITTED     RUN_TIME ST PRI SIZE CMD
	1234.0   username             4/29 16:42   0+00:00:00 I  0   0.0  short.sh
	1234.1   username             4/29 16:42   0+00:00:00 I  0   0.0  short.sh
	1234.2   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
	1234.3   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
	1234.4   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
	1234.5   username             4/29 16:42   0+00:00:00 I  0   0.0  short.sh
	1234.6   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
	1234.7   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
	1234.8   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
	1234.9   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh

	10 jobs; 0 completed, 0 removed, 3 idle, 7 running, 0 held, 0 suspended


#### Job history

Once your jobs have finished, you can get information about its execution
from the **connect client history** command. In this example:


	$ connect client history 1234
 	ID     OWNER          SUBMITTED   RUN_TIME     ST COMPLETED   CMD
	1234.5   username             4/29 16:42   0+00:00:27 C   4/29 16:45 /home/...
	1234.4   username             4/29 16:42   0+00:01:18 C   4/29 16:45 /home/...
	1234.1   username             4/29 16:42   0+00:00:27 C   4/29 16:45 /home/...
	1234.0   username             4/29 16:42   0+00:00:27 C   4/29 16:45 /home/...
	1234.6   username             4/29 16:42   0+00:00:52 C   4/29 16:44 /home/...
	1234.8   username             4/29 16:42   0+00:00:52 C   4/29 16:44 /home/...
	1234.7   username             4/29 16:42   0+00:00:52 C   4/29 16:44 /home/...
	1234.9   username             4/29 16:42   0+00:00:51 C   4/29 16:44 /home/...
	1234.2   username             4/29 16:42   0+00:00:51 C   4/29 16:44 /home/...
	1234.3   username             4/29 16:42   0+00:00:51 C   4/29 16:44 /home/...


Note: You can see much more information about status
using the -long option (e.g. ```connect client history -long 1234```).


#### Retrieve outputs

To retrieve job outputs from the connect server, use **connect client pull**.

	$ connect client pull
	notice: fetching tutorial-quickstart/log/job.log.1234 as log/job.log.1234...
	notice: fetching tutorial-quickstart/log/job.error.1234-7 as log/job.error.1234-7...
	notice: fetching tutorial-quickstart/log/job.output.1234-7 as log/job.output.1234-7...
	notice: fetching tutorial-quickstart/log/job.error.1234-6 as log/job.error.1234-6...
	notice: fetching tutorial-quickstart/log/job.error.1234-5 as log/job.error.1234-5...
	notice: fetching tutorial-quickstart/log/job.output.1234-6 as log/job.output.1234-6...
	notice: fetching tutorial-quickstart/log/job.output.1234-5 as log/job.output.1234-5...
	notice: fetching tutorial-quickstart/log/job.error.1234-9 as log/job.error.1234-9...
	notice: fetching tutorial-quickstart/log/job.output.1234-9 as log/job.output.1234-9...
	notice: fetching tutorial-quickstart/log/job.error.1234-0 as log/job.error.1234-0...
	notice: fetching tutorial-quickstart/log/job.output.1234-0 as log/job.output.1234-0...
	notice: fetching tutorial-quickstart/log/job.error.1234-4 as log/job.error.1234-4...
	notice: fetching tutorial-quickstart/log/job.error.1234-8 as log/job.error.1234-8...
	notice: fetching tutorial-quickstart/log/job.output.1234-4 as log/job.output.1234-4...
	notice: fetching tutorial-quickstart/log/job.output.1234-8 as log/job.output.1234-8...
	notice: fetching tutorial-quickstart/log/job.output.1234-2 as log/job.output.1234-2...
	notice: fetching tutorial-quickstart/log/job.error.1234-3 as log/job.error.1234-3...
	notice: fetching tutorial-quickstart/log/job.error.1234-2 as log/job.error.1234-2...
	notice: fetching tutorial-quickstart/log/job.output.1234-3 as log/job.output.1234-3...
	notice: fetching tutorial-quickstart/log/job.error.1234-1 as log/job.error.1234-1...
	notice: fetching tutorial-quickstart/log/job.output.1234-1 as log/job.output.1234-1...

#### Check the job output

Once your jobs have finished, you can look at the files that HTCondor has
returned to the working directory. If everything was successful, it
should have returned in the `~/tutorial-quickstart/log` directory:

  * log files from Condor for the job cluster:  `job.log.$(Cluster).$(Process)`
  * output files for each job's output: `job.output.$(Cluster).$(Process)`
  * error files for each job's errors: `job.error.$(Cluster).$(Process)`

where `$(Cluster)` will be an integer number (typically a large number)
for this specific submission, and `$(Process)` will number 0...9.

Read one of the output files. It should look something like this:

	$ cat job.output.1234.0
	Start time: Wed Apr 29 17:44:36 EDT 2015
	Job is running on node: MAX-EDLASCH-S3-its-u12-nfs-20141003
	Job running as user: uid=1066(osgconnect) gid=502(condoruser) groups=502(condoruser),108(fuse)
	Job is running in directory: /tmp/rcc_syracuse/rcc.1bNeUskyJl/execute.10.5.70.108-1098/dir_2553

	Working hard...
	Science complete!
	
For this example we see the first job in the submission (1234.0) ran on a free node at Syracuse University.

## Getting Help
For assistance or questions, please email the OSG User Support team  at `user-support@opensciencegrid.org`, direct message tweet to [@osgusers](http://twitter.com/osgusers) or visit the [help desk and community forums](http://support.opensciencegrid.org).



[CI Connect]:http://ci-connect.net/
[OSG Connect]:http://osgconnect.net/
[HTCondor]:http://research.cs.wisc.edu/htcondor/
[Open Science Grid]:http://www.opensciencegrid.org/
[signed up for an account]:http://osgconnect.net/signup
[ConnectBook]:http://osgconnect.net/book

