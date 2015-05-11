#!/bin/bash
#
# @usage @ [-u username] [projectname]
# 
#Marco Mambelli 130820 marco@hep.uchicago.edu
#Lincoln Bryant (lincolnb@hep.uchicago.edu) 
# all Projects have corresponding UNIX groups starting with "@"

PROJECT_BLACKLIST=${connect_blacklist:-/etc/ciconnect/project_blacklist}

function help_msg {
  cat >&2 << EOF
$0 [ -h | -u USER ] [PROJECT]
Prints the projects membership for the user if no PROJECT is provided (exit code 0)
If PROJECT is provided returns 0 if the user is member, 1 otherwise
 -u USER  set the user name (the user running the script by default)
 -q       quiet (prints only the projects list when no project is provided)
 -h       print this help message
EOF
}

me=`whoami`

while getopts hqu: option
do
  case "${option}"
  in
  h) help_msg; exit 2;;
  u) subject=${OPTARG};;
  q) quiet="true";;
  *) help_msg; exit 2;;
  esac
done
shift $((OPTIND-1))

if [ -z "$subject" ]; then
	subject=$me
fi

project="$1"

# Check for project membership if an argument is given
check () {
  user="$1"
  project="$2"

  if egrep "^$project"'$' $PROJECT_BLACKLIST >/dev/null 2>&1; then
    return 1
  fi

  # get memberships, return user's membership in project
  tmp_group=`echo "@$project"`
  echo ,$(getent group $tmp_group | cut -d: -f4), | grep ",$user," 2>&1 > /dev/null
}

if [ -n "$project" ]; then
  check "$subject" "$project"
  RETV=$?
  if [ -z "$quiet" ]; then
    [ $RETV -eq 0 ] &&
      echo "User $subject belongs to project $project" ||
      echo "User $subject does not belong to project $project"
  fi
  exit $RETV
fi

# Return project list
if [ -z $QUIET ]; then
  echo "Based on your username ($subject), here is a list of projects you have"
  echo "access to:"
fi

(
	getent group |
		tr : , |
		sed -e 's/$/,/' |
		grep ,$subject, |
		cut -d, -f1 |
		grep ^[@] |
		sed -e 's/^@//' |
		while read proj; do
			egrep -i "^$proj"'$' $PROJECT_BLACKLIST >/dev/null || echo "  * $proj"
		done |
		sort
	exit $?
)
