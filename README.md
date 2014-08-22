BOSCO module
============

1.0 - directory containing installed BOSCO files 

connect-1.0 - modulefile for BOSCO

setup.sh - setup script

How to test
-----------
1. ssh into user@midway.rcc.uchicago.edu
2. cd privatemodules (try "module load use.own" if the directory does not exist)
3. module load git
4. git clone https://github.com/SISC2014/Bosco-Module.git
5. mv Bosco-Module connect
6. cp -r connect/1.0 ~/bosco
7. mkdir -p ~/lib/connect/extensions
8. cp connect/setup.sh ~/lib/connect/extensions/setup.sh
9. module load use.own
10. module load connect
11. connect setup
12. enter your ssh user/password to UChicago Connect when prompted

Bosco should be set up, with the UChicago Connect cluster added. Run "condor_submit" to submit jobs (currently supports grid universe only) and "condor_q" to check jobs. 
