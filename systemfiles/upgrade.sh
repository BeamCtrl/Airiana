#!/bin/bash
#usage upgrade.sh [current release codename] [next release codename]
# test to make sure there are two arguments
if [ $# -ne 2 ]
then
  exit 2
fi
osname=`./osname.py`

#set headless
export DEBIAN_FRONTEND=noninteractive
export DEBIAN_PRIORITY=critical

#Get the latest from current distro release
sudo -E apt-get -q update
sudo -E apt-get -q update --fix-missing
sudo -E apt-get -yq upgrade --download-only

if [ "$osname" == "jessie" ]
then
sudo -E apt-get -yq --force-yes  -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" upgrade
fi

if [ "$osname" == "stretch" ]
then
sudo -E apt-get -yq -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" upgrade
fi

sudo apt --fix-broken install
sudo -E apt-get -yq autoremove
sudo -E apt-get -yq autoclean

#update the distro sources
apt=$(sed "s/$1/$2/g" /etc/apt/sources.list)
sudo echo $apt |sudo tee  /etc/apt/sources.list
apt2=$(sed "s/$1/$2/g" /etc/apt/sources.list.d/raspi.list)
sudo echo $apt2 |sudo tee  /etc/apt/sources.list.d/raspi.list

# update/upgrade/dist-upgrade
sudo -E apt-get -q update
sudo -E apt-get update --fix-missing
sudo -E apt-get -yq upgrade --download-only
if [ "$osname" == "jessie" ]
then
sudo -E apt-get -yq --force-yes  -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" dist-upgrade
fi

if [ "$osname" == "stretch" ]
then
sudo -E apt-get -yq  --allow-downgrades --allow-remove-essential --allow-change-held-packages --allow-releaseinfo-change -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" dist-upgrade
fi


sudo -E apt-get update --fix-missing
sudo apt --fix-broken install
sudo -E apt-get -yq autoremove
sudo -E apt-get -yq autoclean

