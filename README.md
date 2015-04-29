Installation
============

Connect Client is the set of programs and files for linking a campus
cluster to a CI Connect instance such as OSG Connect. Connect Client can be installed 
by an individual user or by the HPC administrator for system-wide usage.

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
-------------------------------

Choose a directory to install Connect Client into.  A reasonable choice
is `~/software/connect`.  Also choose a directory to
install the software module into.  A reasonable choice for this on
is `~/privatemodules`.  Then run `./install.sh` with these
two directories and a version number (e.g. 0.2):

    $ ./install.sh ~/software/connect-client ~/privatemodules 0.2


Installation by a site administrator
---------------------------------------

Typically this would be quite similar, only system paths would be used:

    $ ./install.sh -site /software/connect-client /software/modulefiles 0.2


Using Connect Client
====================

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
================

Each user must perform this setup step once before using
OSG Connect the first time.  

    $ module load connect-client
    $ connect client setup
    <enter your OSG Connect username and password when prompted>

The Connect Client should be set up, with the OSG Connect site
added. Run `connect client submit` to submit jobs, `connect client q`
to check jobs. 


User Guide 
==========

### Login

To begin, log in to your cluster's login node.

	$ ssh username@login.mycluster.edu   # [correct details for your site]


### Set up Connect

Once logged in, set up the Connect program with the following step:

	$ module load connect-client

If your site doesn't use environment modules, you may need to adjust your
$PATH; see above.

Now you will have access to all of the Connect program plugins. For
a list of available plugins, enter the following command:

	$ connect client

To run any of these plugins, just enter "connect client [plugin name]".


### Example job 

Now let's create a test script to execute as your job submission to
OSG Connect. Create a working directory that will be synched with the
remote host on OSG Connect.  

        $ mkdir working-dir
        $ cd workding-dir
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

	$ chmod +x short.sh


### Create an HTCondor submit file

Create a simple HTCondor submit file, called tutorial.submit

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
Error = job.error
Output = job.output

# The LOG file is where HTCondor places information about your
# job's status, success, and resource consumption.
Log = job.log

# QUEUE is the "start button" - it launches any jobs that have been
# specified thus far.
Queue 1
````

### Submit the job

Submit the job using **connect client submit**.
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


### Check job status
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


### Job history

Once your job has finished, you can get information about its execution
from the **connect client history** command:

````
$ connect client history 1
 ID      OWNER            SUBMITTED     RUN_TIME ST   COMPLETED CMD
 1.0   username            8/25 10:06   0+00:00:12 C   8/25 10:06 short.sh
````

Note: You can see much more information about your job's final status
using the -long option (e.g. "connect client history -long 1").



### Retrieve outputs

To retrieve job outputs from the connect server, use **connect client pull**.

````
$ connect client pull
...
````


### Check the job output

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
