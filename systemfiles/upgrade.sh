sed "s/$1/$2/g" /etc/apt/sources.list > /etc/apt/sources.list
export DEBIAN_FRONTEND=noninteractive
export DEBIAN_PRIORITY=critical
apt-get -qy update
apt-get -y -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" upgrade
apt-get -qy autoremove
apt-get -qy autoclean
apt-get -y -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confnew" dist-upgrade
