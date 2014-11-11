switch_modules () {

  shell=`basename \`ps -p $$ -ocomm=\``
  case $1 in 
  oasis) 
    unload_modules
    . /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/$shell
    ;;
  local)
    unload_modules
     . /srv/adm/modules/init/$shell
    ;;
  esac
}

unload_modules () {
  next_token=0
  for i in `module list 2>&1`;
  do
    if [[ "$next_token" == "1" ]];
    then
      module unload $i
      next_token=0
    fi
    if grep -q ')' <<< $i;
    then
      next_token=1
    fi
done
}
