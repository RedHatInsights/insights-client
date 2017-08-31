rm etc/rpm.egg
rm etc/rpm.egg.asc

CWD=$(pwd)
DO_INSTALL=false

if [[ -f "/etc/insights-client/rpm.egg" ]]; then
  rm /etc/insights-client/rpm.egg
else
  DO_INSTALL=true
fi

if [[ -z $1 ]]; then
  if [[ -d "../insights-core" ]]; then
    cd ../insights-core
  else
    echo "../insights-core not found. Please specify a directory where the insights-core repo is located"
    exit
  fi
else
  if [[ -d "$1" ]]; then
    cd $1
  else
    echo "Please specify a valid directory."
    exit
  fi
fi

python setup.py -q bdist_egg

if [[ $DO_INSTALL = true ]]; then
  mv dist/*.egg $CWD/etc/rpm.egg
  cd $CWD
  touch etc/rpm.egg.asc
  sudo yum remove -y insights-client
  make clean
  make install
else
  mv dist/*.egg /etc/insights-client/rpm.egg
  cd $CWD
fi
exit
