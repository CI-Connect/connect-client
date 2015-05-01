Introduction
============
Connect Client is the set of programs and files for linking a campus
research computing cluster to a [CI Connect] instance, such as [OSG Connect], 
which uses [HTCondor] to submit jobs to the [Open Science Grid].  The 
example below assumes one has already [signed up for an account] on OSG Connect.

Installation
============
Connect Client can be installed by an individual user or by the HPC administrator for 
system-wide usage.

Obtaining the Connect Client distribution
-----------------------------------------

Regardless of which installation path you follow, the first step is the same:

    $ ssh login.mycluster.edu            # [your cluster site here]
    $ module load git                    # [if needed]
    $ git clone --recursive https://github.com/CI-Connect/connect-client
    $ cd connect-client

This obtains a copy of the distribution and sets your shell's working
directory to that copy.

Installation by an individual user
----------------------------------

Choose a directory to install Connect Client into.  A reasonable
choice is `~/software/connect`.  Also choose a directory for the
module descrption information.  A reasonable choice for this on
`~/privatemodules`.  Then run `./install.sh` with these two directories
and a version number (e.g. 0.2):

    $ ./install.sh ~/software/connect-client ~/privatemodules 0.2


Installation by a site administrator
------------------------------------

Typically this would be quite similar, only system paths would be used, for example:

    $ ./install.sh -site /software/connect-client /software/modulefiles 0.2


Setting up Connect Client
=========================

Using environment modules
----------------------------

To make Connect Client available, use the `module` command as you would
any other software module.  

    $ module load connect-client

For user installations with modules, you'll need to load the `use.own` module first:

    $ module load use.own
    $ module load connect-client


Without environment modules
---------------------------

If your site does not have environment modules, install the package as above and modify the $PATH:

    $ export PATH=~/software/connect-client/bin:$PATH
    

First-time setup
----------------
Each user must perform this setup step once before using
OSG Connect the first time.  

    $ connect client setup
    <enter your OSG Connect username and password when prompted>

The Connect Client should be set up, with the OSG Connect site
added. Test the setup with:

    $ connect client test


User Guide 
==========

Connect Client commands
-------------------------

For a list of available commands, enter the following:

	$ connect client
       	usage: 	connect client [opts] <subcommand> [args]
       		connect client [opts] dag <dagfile>
       		connect client [opts] history <condor_history arguments>
       		connect client [opts] pull [[localdir] remotedir]
       		connect client [opts] push [[localdir] remotedir]
       		connect client [opts] q <condor_q arguments>
       		connect client [opts] rm <condor_rm arguments>
       		connect client [opts] revoke
       		connect client [opts] run <condor_run arguments>
       		connect client [opts] setup [--replace-keys] [servername]
       		connect client [opts] status <condor_status arguments>
       		connect client [opts] submit <submitfile>
       		connect client [opts] sync [[localdir] remotedir]
       		connect client [opts] test [servername]
       		connect client [opts] wait <condor_wait arguments>

	opts:
    		-s|--server hostname       set connect server name
    		-u|--user username         set connect server user name
    		-r|--remote directory      set connect server directory name
            -v|--verbose               show additional information

	
To run any of these commands, just enter ````connect client [opts] [command name]````.


### Example submission

Now let's create a test script for execution of 10 jobs on the OSG.
*Create working directory (and logfile subdirectory)* that will be synched with the remote host on OSG Connect.  

	$ mkdir ~/working-dir
	$ mkdir ~/working-dir/log
	$ cd ~/workding-dir
	$ nano short.sh

````bash
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
````

Make the script executable.

	$ chmod +x short.sh


### Create the HTCondor submit description file

Create a simple HTCondor submit description file, called tutorial.submit

	$ nano tutorial.submit

The submit file should contain the following:
````
# The UNIVERSE defines an execution environment. 
universe = vanilla

# EXECUTABLE is the program your job will run. It's often useful
# to create a shell script to "wrap" your actual work.
Executable = short.sh

# ERROR and OUTPUT are the error and output channels from your job
# that HTCondor returns from the remote host.
Error = log/job.error.$(Cluster)-$(Process)
Output = log/job.output.$(Cluster)-$(Process)

# The LOG file is where HTCondor places information about your
# job's status, success, and resource consumption.
Log = log/job.log.$(Cluster)-$(Process)

# QUEUE is the "start button" - it launches any jobs that have been
# specified thus far.
Queue 10
````

Here, ```$(Cluster)``` labels the submission (called "Cluster ID") and ```$(Process)``` labels individual jobs. 


### Submit the script

Submit the script using **connect client submit**.
````
$ connect client submit tutorial.submit
Submitting job(s).
1 job(s) submitted to cluster 1.
````

**N.B. If your OSG Connect username differs from your local username,
you will need an additional option for all connect client commands.**
This will be remedied soon.**

Submit the job using **connect client submit**.
````
$ connect client -u <osg-connect-username> submit tutorial.submit
Submitting job(s).
1 job(s) submitted to cluster 1.
````


### Check job queue
The **connect client q** command tells the status of submitted jobs:

````
$ connect client q <your-remote-username>

-- Submitter: login01.osgconnect.net : <192.170.227.195:40814> : login01.osgconnect.net
 ID      OWNER            SUBMITTED     RUN_TIME ST PRI SIZE CMD
9067914.0   username             4/29 16:42   0+00:00:00 I  0   0.0  short.sh
9067914.1   username             4/29 16:42   0+00:00:00 I  0   0.0  short.sh
9067914.2   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
9067914.3   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
9067914.4   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
9067914.5   username             4/29 16:42   0+00:00:00 I  0   0.0  short.sh
9067914.6   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
9067914.7   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
9067914.8   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh
9067914.9   username             4/29 16:42   0+00:00:49 R  0   0.0  short.sh

10 jobs; 0 completed, 0 removed, 3 idle, 7 running, 0 held, 0 suspended
````

### Job history

Once your jobs have finished, you can get information about its execution
from the **connect client history** command. In this example:

````
$ connect client history 9067914
 ID     OWNER          SUBMITTED   RUN_TIME     ST COMPLETED   CMD
9067914.5   rwg             4/29 16:42   0+00:00:27 C   4/29 16:45 /home/...
9067914.4   rwg             4/29 16:42   0+00:01:18 C   4/29 16:45 /home/...
9067914.1   rwg             4/29 16:42   0+00:00:27 C   4/29 16:45 /home/...
9067914.0   rwg             4/29 16:42   0+00:00:27 C   4/29 16:45 /home/...
9067914.6   rwg             4/29 16:42   0+00:00:52 C   4/29 16:44 /home/...
9067914.8   rwg             4/29 16:42   0+00:00:52 C   4/29 16:44 /home/...
9067914.7   rwg             4/29 16:42   0+00:00:52 C   4/29 16:44 /home/...
9067914.9   rwg             4/29 16:42   0+00:00:51 C   4/29 16:44 /home/...
9067914.2   rwg             4/29 16:42   0+00:00:51 C   4/29 16:44 /home/...
9067914.3   rwg             4/29 16:42   0+00:00:51 C   4/29 16:44 /home/...
````

Note: You can see much more information about status
using the -long option (e.g. ```connect client history -long 9067914```).


### Retrieve outputs

To retrieve job outputs from the connect server, use **connect client pull**.

````
$ connect client pull
...
````


### Check the job output

Once your jobs have finished, you can look at the files that HTCondor has
returned to the working directory. If everything was successful, it
should have returned in the ````~/working-dir/log```` directory:

  * log files from Condor for the job cluster: ````job.log.$(Cluster).$(Process)````
  * output files for each job's output: ````job.output.$(Cluster).$(Process)````
  * error files for each job's errors: ````job.error.$(Cluster).$(Process)````

where ````$(Cluster)```` will be a large integer number for this specific submission, and ````$(Process)```` will number 0...10.

Read one of the output files. It should look something like this:

````
$ cat job.output.9067914-0
Start time: Wed Apr 29 17:44:36 EDT 2015
Job is running on node: MAX-EDLASCH-S3-its-u12-nfs-20141003
Job running as user: uid=1066(osgconnect) gid=502(condoruser) groups=502(condoruser),108(fuse)
Job is running in directory: /tmp/rcc_syracuse/rcc.1bNeUskyJl/execute.10.5.70.108-1098/dir_2553

Working hard...
Science complete!
````

[CI Connect]:http://ci-connect.net/
[OSG Connect]:http://osgconnect.net/
[HTCondor]:http://research.cs.wisc.edu/htcondor/
[Open Science Grid]:http://www.opensciencegrid.org/
[signed up for an account]:http://osgconnect.net/signup


