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

sudo apt-get purge -yq wolfram-engine libreoffice* apt-listchanges scratch scratch2
#Get the latest from current distro release
sudo -E apt-get -q update
sudo -E apt-get -q update --fix-missing
sudo -E apt-get -yq upgrade --download-only || exit 1

if [ "$osname" == "jessie" ]
then
sudo -E apt-get -yq --force-yes  -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" upgrade
fi

if [ "$osname" == "stretch" ]
then
sudo -E apt-get -yq --allow-downgrades --allow-change-held-packages -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" upgrade
fi

if [ "$osname" == "buster" ]
then
sudo -E apt-get -yq --allow-downgrades --allow-change-held-packages -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" upgrade
fi



sudo apt --fix-broken install
sudo -E apt-get -yq autoremove
sudo -E apt-get -yq autoclean

#update the distro sources
apt=$(sed "s/$1/$2/g" /etc/apt/sources.list)
sudo echo $apt |sudo tee  /etc/apt/sources.list
apt2=$(sed "s/$1/$2/g" /etc/apt/sources.list.d/raspi.list)
sudo echo $apt2 |sudo tee  /etc/apt/sources.list.d/raspi.list

# update/upgrade/dist-upgrade sudo -E apt-get -yq --allow-remove-essential --allow-change-held-packages -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" upgrade

sudo -E apt-get -q update
sudo -E apt-get update --fix-missing
sudo -E apt-get -yq upgrade --download-only || exit

if [ "$osname" == "jessie" ]
then
sudo -E apt-get -yq --force-yes  -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" dist-upgrade\
 || sudo apt -yq --force-yes -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" --fix-broken install
fi

if [ "$osname" == "stretch" ]
then
  # set default replies to smb configurations
  echo "samba-common samba-common/workgroup string  WORKGROUP" | sudo debconf-set-selections
  echo "samba-common samba-common/dhcp boolean true" | sudo debconf-set-selections
  echo "samba-common samba-common/do_debconf boolean true" | sudo debconf-set-selections
  sudo -E apt-get -yq  --allow-downgrades --allow-remove-essential --allow-change-held-packages\
    -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" dist-upgrade\
   || sudo apt -yq -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" --fix-broken install
fi

if [ "$osname" == "buster" ]
then
sudo -E apt-get -yq  --allow-downgrades --allow-remove-essential --allow-change-held-packages\
  -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" dist-upgrade\
 || sudo apt -yq -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" --fix-broken install
fi


sudo -E apt-get update --fix-missing
sudo -E apt-get -yq autoremove
sudo -E apt-get -yq autoclean
