BOSCO module
============

1.0 - directory containing installed BOSCO files 

connect-1.0 - modulefile for BOSCO

connect.sh - setup script

How to test
-----------
1) ssh into user@midway.rcc.uchicago.edu
2) run "module load use.own"
3) cd privatemodules
4) git clone https://github.com/SISC2014/Bosco-Module.git
4) rename Bosco-Module to connect
5) cp connect/1.0 ~/bosco
6) cp connect/connect.sh ~/bosco/connect.sh
7) module load connect
8) enter your ssh user/password to UChicago Connect when prompted
9) Bosco should be set up, with the UChicago Connect cluster added 
