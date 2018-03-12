#!/bin/sh -xe

# Thanks to:
# https://github.com/opensciencegrid/htcondor-ce/tree/master/tests

OS_VERSION=$1
PY_VER=$2

echo OS_VERSION $OS_VERSION
echo PY_VER $PY_VER

ls -l $PWD

# Clean the yum cache
yum -y clean all
yum -y clean expire-cache
yum -y install root root-\*

uname -a

export BUILD_HOME=/home/daqbuild

cd ${BUILD_HOME}/gem-plotting-tools
# git clone https://github.com/cms-gem-daq-project/gembuild.git config

pyexec=$(which ${PY_VER})
echo Trying to test with ${pyexec}

pip install --user -U setuptools pip

make

make rpm

if [ -f "$pyexec" ]
then
    virtualenv ~/virtualenvs/${PY_VER} -p ${pyexec} --system-site-packages
    . ~/virtualenvs/${PY_VER}/bin/activate
    pip install -r requirements.txt
    pip install codecov
    coverage run python
    codecov
    bash <(curl -s https://codecov.io/bash) && echo "Uploaded code coverage"
    deactivate
fi
