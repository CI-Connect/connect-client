BOSCO module
============

1.0 - directory containing installed BOSCO files 

connect-1.0 - modulefile for BOSCO

connect.sh - setup script

How to test
-----------
1. ssh into user@midway.rcc.uchicago.edu
2. cd privatemodules (try "module load use.own" if the directory does not exist)
3. module load git
4. git clone https://github.com/SISC2014/Bosco-Module.git
5. mv Bosco-Module connect
6. chmod +x connect/1.0/connect.sh
7. cp -r connect/1.0 ~/bosco
8. module load use.own
9. module load connect
10. enter your ssh user/password to UChicago Connect when prompted
11. Bosco should be set up, with the UChicago Connect cluster added 
