#! /bin/env python

import os
import sys
import datetime
from hashlib import sha1
import subprocess
import getpass
import htcondor
import re

sys.path.insert(0, '/cvmfs/cms.cern.ch/crab/CRAB_2_11_1_patch1/python/')
from DashboardAPI import apmonSend, apmonFree

#import DashboardAPI
#DashboardAPI.apmonLoggingLevel = "DEBUG"

class CMSReporter(object):
    def __init__(self, submitfile):
        self._submitfile = submitfile
        self._cancel_report = False
        self._wrapper = '/home/khurtado/CMSConnect/dashboard/connect_wrapper.py'

        # Create and register monitor
        self._taskid = self._get_taskid(str(submitfile))
        self.monitor = Monitor(self._taskid)

    def _preppend_to_item_values(self, sub, key, value, separator=' '):
        '''Search for all coincidences of a key in the submit class
        and preppend 'value' to its contents.
        '''
        index = 0
        for item in sub:
            if key.lower() in item[0].lower():
                item = (item[0], '{0}{1}{2}'.format(value, separator, item[1]))
                list.__setitem__(sub, index, item)
            index += 1

    def _search_key_values(self, sub, key):
        '''Search for all coincidences of a key in the submit class.
        Returns a list with each key position
        '''
        index = 0
        key_map = []
        for item in sub:
            if key.lower() in item[0].lower():
                key_map.append(index)
            index += 1
        return key_map

    def _split_by_exe_blocks(self, sub):
        # Ignore first executable position
        blocks = [0] + self._search_key_values(sub, 'executable')[1:] + [len(sub)]
        sublists = []
        for i in range(len(blocks)-1):
            sublists += [ sub[blocks[i]:blocks[i+1]] ]

        return sublists

    def _modify_exe_args(self, sub):
        '''Return a copy of a modified submit object. Modifications are:
            -Replace 'Executables' for 'connect_wrapper.py'
            -Preppend the original executable to arguments
              -Create one if there are no arguments
            -Add executable to transfer_input_files
              -Create one if there is no such attribute
            -Do this per executable block
        '''
        newsub = sub.__class__()
        latest_transfer_input_files = ''

        for sublist in self._split_by_exe_blocks(sub):
            sublist = sub.__class__(sublist)
            Executable = True if 'executable' in sublist else False
            if Executable:
                exe_index = int(sublist.index(sublist['executable']))
                exe_cmd = sublist['executable'][1]
                sublist['executable'] = self._wrapper
                # Update arguments
                if 'arguments' in sublist:
                    self._preppend_to_item_values(sublist, 'arguments', exe_cmd)
                else:
                    #sublist['arguments'] = exe_cmd
                    sublist.insert(exe_index+1,('Arguments', exe_cmd))
                # Update transfer_input_files
                if 'transfer_input_files' in sublist:
                    latest_transfer_input_files = sublist['transfer_input_files'][1]
                    self._preppend_to_item_values(sublist, 'transfer_input_files', exe_cmd,',')
                else:
                    if latest_transfer_input_files:
                        sublist.insert(exe_index+1, ('transfer_input_files', '{0},{1}'.format(exe_cmd, latest_transfer_input_files)))
                    else:
                        sublist.insert(exe_index+1, ('transfer_input_files', exe_cmd))
                newsub.extend(sublist)
        newsub.update()
        return newsub


    def _get_taskid(self, jdl_name):
        filename = os.path.splitext(jdl_name)[0]
        taskid = 'cmsconnect_{0}_{1}_{2}'.format(getpass.getuser(), filename,
                                                 sha1(str(datetime.datetime.utcnow())).hexdigest()[-16:])
        return taskid


    def _cluster_jobs(self, output):
        cluster_jobs = []
        cluster_re = re.compile(r'(\d+) job\(s\) submitted to cluster (\d+)\.')
        for line in output.split("\n"):
            match = cluster_re.match(line)
            if match:
                cluster_jobs.append((match.group(2), match.group(1)))

        return cluster_jobs

    def report_jobs(self, condor_output):
        if self._cancel_report:
            return

        clusters = self._cluster_jobs(condor_output)
        if not clusters:
            print "Warning: Could not extract clusters and jobs submitted information."
            return

        jobs_previous = 0
        schedd = htcondor.Schedd()

        for cluster, jobs in clusters:
            for procid in range(int(jobs)):
                new_id = str(int(jobs_previous) + int(procid))
                schedd.edit(['{0}.{1}'.format(cluster, procid)], 'Dashboard_Id', new_id)
                schedd.edit(['{0}.{1}'.format(cluster, procid)], 'Environment',
                        "\"{0} Dashboard_Id='{1}'\"".format(self.monitor.environment,new_id))
            jobs_previous+=int(jobs)

        # Report jobs
        njobs = jobs_previous
        for id in range(0, int(njobs)):
            self.monitor.register_job(str(id))
        self.monitor.free()

        for id in range(0, int(njobs)):
            self.monitor.update_job(str(id), 'Pending')

        return


    def cms_dashboard_report(self, sub, classads, nargs):
        ''' - Register jobs to monitor(s).
              - One monitor per Executable
            - Add dashboard parameters to Classads and SHELL environment.
            - Preppend dashboard wrapper before executable for the worker node.
            Inputs:
                -sub: This is the submit jdl file interpreted by the condor_submit::submit
                      class and passed as an object.
                -submitfile: Is the condor submit filename.
                -classads: Condor ClassAds to modify.
                -nargs: Arguments parsed to condor from condor_submit wrapper.
        '''
        original_sub = sub
        sub = sub.__class__(self._modify_exe_args(sub))
        if sub:
            sub.update()
        else:
            print """Warning: Could not append dashboard wrapper to submit file.
            Stop CMS dashboard reporting"""
            self._cancel_report = True

            return original_sub

        # Create and register monitor
        self.monitor.set_executable(sub['executable'][1])
        self.monitor.register_run()
        dashboard_monitorid, dashboard_syncid = self.monitor.generate_ids('MetaID')
        dashboard_parameters = [("Dashboard_taskid", self._taskid),
                                ("Dashboard_monitorid", dashboard_monitorid),
                                ("Dashboard_syncid", dashboard_syncid),
                                ]
        classads += dashboard_parameters
        # Add dashboard paramenters to the SHELL environment
        envpars =  ' '.join("{0}='{1}'".format(ad, value) for ad, value in dashboard_parameters)
        # envpars += ' Dashboard_Id=$(Process)'
        nargs += ['-a', '+environment="{0}"'.format(envpars)]
        self.monitor.environment = envpars

        return sub


class Monitor(object):

    def __init__(self, taskid):
        self._taskid = taskid
        p = subprocess.Popen(["voms-proxy-info", "-identity"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        id, err = p.communicate()
        id = id.strip()
        self.__fullname = id.rsplit('/CN=', 1)[1]
        self.__username = u'unknown'
        self.__cmssw_version = "unknown"
        #self.__executable = "unknown"
        self.__executable = "unknown"

    def generate_ids(self, jobid):
        monitorid = '{0}_{1}/{0}'.format(jobid, 'https://login.uscms.org/{0}'.format(sha1(self._taskid).hexdigest()[-16:]))
        syncid = 'https://login.uscms.org//{0}//12345.{1}'.format(self._taskid, jobid)

        return monitorid, syncid

    def free(self):
        apmonFree()

    def register_run(self):
        apmonSend(self._taskid, 'TaskMeta', {
            'taskId': self._taskid,
            'jobId': 'TaskMeta',
            'tool': 'cmsconnect',
            'tool_ui': os.environ.get('HOSTNAME', ''),
            'SubmissionType': 'direct',
            'JSToolVersion': '3.2.1',
            'scheduler': 'condor',
            'GridName': '/CN=' + self.__fullname,
            'ApplicationVersion': self.__cmssw_version,
            'taskType': 'analysis',
            'vo': 'cms',
            'user': self.__username,
            'CMSUser': self.__username,
            'datasetFull': '',
            'resubmitter': 'user',
            'exe': self.__executable
            })
        self.free()


    def register_job(self, id):
        monitorid, syncid = self.generate_ids(id)
        apmonSend(self._taskid, monitorid, {
            'taskId': self._taskid,
            'jobId': monitorid,
            'sid': syncid,
            'broker': 'condor',
            'bossId': str(id),
            'SubmissionType': 'Direct',
            'TargetSE': 'cmseos.fnal.gov',
            'localId': '',
            'tool': 'cmsconnect',
            'JSToolVersion': '3.2.1',
            'tool_ui': os.environ.get('HOSTNAME', ''),
            'scheduler': 'condor',
            'GridName': '/CN=' + self.__fullname,
            'ApplicationVersion': self.__cmssw_version,
            'taskType': 'analysis',
            'vo': 'cms',
            'user': self.__username,
            'CMSUser': self.__username,
            # 'datasetFull': self.datasetPath,
            'resubmitter': 'user',
            'exe': self.__executable
            })
        return monitorid, syncid

    def update_job(self, id, status):
        monitorid, syncid = self.generate_ids(id)
        apmonSend(self._taskid, monitorid, {
            'taskId': self._taskid,
            'jobId': monitorid,
            'sid': syncid,
            'StatusValueReason': '',
            'StatusValue': status,
            'StatusEnterTime':
            "{0:%F_%T}".format(datetime.datetime.utcnow()),
            'StatusDestination': 'unknown',
            'RBname': 'condor'
            })
        #apmonFree()

    def set_executable(self, executable):
        self.__executable = executable

    @property
    def environment(self):
        return self._environment

    @environment.setter
    def environment(self, environ):
        self._environment = environ
