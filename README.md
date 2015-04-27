
Installation
============

Connect Client is the set of programs and files for linking a campus
cluster to a CI Connect instance.  Currently it is developed on and for
the University of Chicago Research Computing Cluster (RCC) and RCC
Connect, but the goal is to extend the toolchain to accomodate the
peculiarities of other sites as well.

Connect Client can be installed by an individual user, or sitewide
by the site administrator.

Obtaining the Connect Client distribution
-----------------------------------------

Regardless of which installation path you follow, the first step is
the same:

    sh$ ssh midway.rcc.uchicago.edu   # [your cluster site here]
    sh$ module load git               # [if needed]
    sh$ git clone --recursive https://github.com/CI-Connect/connect-client
    sh$ cd connect-client

This obtains a copy of the distribution and sets your shell's working
directory to that copy.

Installation for the individual
-------------------------------

Choose a directory to install Connect Client into.  A reasonable choice
on RCC/Midway is `~/software/connect`.  Also choose a directory to
install the software module into.  A reasonable choice for this on
RCC/Midway is `~/privatemodules`.  Then run `./install.sh` with these
two directories and a version number:

    sh$ ./install.sh ~/software/connect-client ~/privatemodules 1.0

### Using Connect Client after individual installation

#### Using environment modules

To make Connect Client available, use the `module` command as you would
any other software module on RCC -- with the exception that you will also
need to load the `use.own` module.

    sh$ module load use.own
    sh$ module load connect-client/1.0

#### Without environment modules

If your site does not have environment modules, you'll need to add the
software to your $PATH in another way, such as:

	sh$ export PATH=~/software/connect-client/bin:$PATH

You should now have access to the Connect commands.


Installation for the site administrator
---------------------------------------

Likewise, choose a directory to install Connect Client into.  A
reasonable choice is `/software/connect`.  Also choose a directory to
install the software module into.  A reasonable choice for this at RCC
is `/software/modulefiles`.  Then run `./install.sh` with these two
directories and a version number:

    sh$ ./install.sh /software/connect-client /software/modulefiles 1.0


### Using Connect Client after site installation

This is almost the same as for individual installation, but slightly simpler:

    sh$ module load connect-client/1.0


First-time setup
================

Each user of UChicago Connect must perform this setup step once before
using RCC Connect for the first time.  Before doing so, be sure to
load the module as described above in "Using Connect Client after
installation":

    sh$ module load connect-client
    sh$ connect client setup
    <enter your OSG Connect username and password when prompted>

The Connect Client should be set up, with the OSG Connect site
added. Run `connect client submit` to submit jobs, `connect client q`
to check jobs. 


User Guide 
==========

## Login to Midway

To begin, log in to your cluster's login node.

	$ ssh username@midway.rcc.uchicago.edu   # [correct details for your site]


## Set up Connect

Once logged in to Midway, set up the Connect program with the following step:

	$ module load connect-client

If your site doesn't use environment modules, you may need to adjust your
$PATH; see above.

Now you will have access to all of the Connect program plugins. For
a list of available plugins, enter the following command:

	$ connect

To run any of these plugins, just enter "connect [plugin name]".

    sh$ connect client setup
    <enter your OSG Connect username and password when prompted>

The command will ask for your ssh password to access OSG Connect. Once
the setup is over, you will be able to submit jobs.


## Example job 

Now let's create a test script to execute as your job submission to
OSG Connect. Create the following script, titled short.sh: 

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

Now, make the script executable.

	sh$ chmod +x short.sh


## Run the job locally

When setting up a new job type, it's important to test your job locally
before submitting it into the grid.

````bash
$ ./short.sh
Start time: Mon Aug 25 10:21:35 CDT 2014
Job is running on node: midway-login1
Job running as user: uid=54161(netid) gid=1000(users) groups=1000(users),10008(rcc)
Job is running in directory: /home/netid
Working hard...
Science complete!
````

## Create an HTCondor submit file

Now, let's create a simple (if verbose) HTCondor submit file, called tutorial.submit

	sh$ nano tutorial.submit

The submit file should contain the following:
````
# The UNIVERSE defines an execution environment. 
universe = vanilla

# EXECUTABLE is the program your job will run. It's often useful
# to create a shell script to "wrap" your actual work.
Executable = short.sh

# ERROR and OUTPUT are the error and output channels from your job
# that HTCondor returns from the remote host.
Error = job.error
Output = job.output

# The LOG file is where HTCondor places information about your
# job's status, success, and resource consumption.
Log = job.log

# QUEUE is the "start button" - it launches any jobs that have been
# specified thus far.
Queue 1
````

## Submit the job

Submit the job using **connect client submit**.
````
$ connect client submit tutorial.submit
Submitting job(s).
1 job(s) submitted to cluster 1.
````

## Check job status
The **connect client q** command tells the status of currently running jobs.

````
$ connect client q <your-remote-username>
-- Submitter: midway-login1.rcc.local : <128.135.112.71:65045?sock=7603_c271_4> : midway-login1.rcc.local
 ID      OWNER            SUBMITTED     RUN_TIME ST PRI SIZE CMD               
   1.0   username         8/25 10:06   0+00:00:06 R  0   0.0  short.sh         

1 jobs; 0 completed, 0 removed, 0 idle, 1 running, 0 held, 0 suspended
````

Let's wait for your job to finish - that is, for **q** not to show the
job in its output. Just keep running **connect client q** until you see
no output. When your job has completed, it will disappear from the list.


## Job history

Once your job has finished, you can get information about its execution
from the **connect client history** command:

````
$ connect client history 1
 ID      OWNER            SUBMITTED     RUN_TIME ST   COMPLETED CMD
 1.0   username            8/25 10:06   0+00:00:12 C   8/25 10:06 short.sh
````

Note: You can see much more information about your job's final status
using the -long option (e.g. "connect client history -long 1").



## Retrieve outputs

To retrieve job outputs from the connect server, use **connect client pull**.

````
$ connect client pull
...
````


## Check the job output

Once your job has finished, you can look at the files that HTCondor has
returned to the working directory. If everything was successful, it
should have returned:

  * a log file from Condor for the job cluster: job.log
  * an output file for each job's output: job.output
  * an error file for each job's errors: job.error

Read the output file. It should look something like this:

````
$ cat job.output
Start time: Mon Aug 25 10:06:12 CDT 2014
Job is running on node: appcloud01
Job running as user: uid=58704(osg) gid=58704(osg) groups=58704(osg)
Job is running in directory: /var/lib/condor/execute/dir_2120
Working hard ...
Science complete!
````
