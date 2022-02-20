#set headless 
export DEBIAN_FRONTEND=noninteractive
export DEBIAN_PRIORITY=critical

#Get the latest from current distro release
sudo -E apt-get -y update
sudo -E apt-get -y -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" upgrade
sudo -E apt-get -y autoremove
sudo -E apt-get -y autoclean

#update the distro sources
apt=`sed "s/$1/$2/g" /etc/apt/sources.list`
sudo echo $apt > /etc/apt/sources.list
apt2=`sed "s/$1/$2/g" /etc/apt/sources.list`
sudo echo $apt2 > /etc/apt/sources.list.d/raspi.list

# update/upgrade/dist-upgrade
sudo -E apt-get -y update
sudo -E apt-get -y -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" upgrade
sudo -E apt-get -y --fix-broken install
sudo -E apt-get -y autoremove
sudo -E apt-get -y autoclean
sudo -E apt-get -y -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" dist-upgrade
sudo -E apt-get -y autoremove
sudo -E apt-get -y autoclean

