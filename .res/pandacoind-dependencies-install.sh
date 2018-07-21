# Used on Debian 9
wget http://ftp.us.debian.org/debian/pool/main/b/boost1.55/libboost-system1.55.0_1.55.0+dfsg-3_amd64.deb
dpkg -i libboost-system1.55.0_1.55.0+dfsg-3_amd64.deb
wget http://ftp.us.debian.org/debian/pool/main/b/boost1.55/libboost-filesystem1.55.0_1.55.0+dfsg-3_amd64.deb
dpkg -i libboost-filesystem1.55.0_1.55.0+dfsg-3_amd64.deb
wget http://ftp.us.debian.org/debian/pool/main/b/boost1.55/libboost-program-options1.55.0_1.55.0+dfsg-3_amd64.deb
dpkg -i libboost-program-options1.55.0_1.55.0+dfsg-3_amd64.deb
wget http://ftp.us.debian.org/debian/pool/main/b/boost1.55/libboost-atomic1.55.0_1.55.0+dfsg-3_amd64.deb
dpkg -i libboost-atomic1.55.0_1.55.0+dfsg-3_amd64.deb
wget http://ftp.us.debian.org/debian/pool/main/b/boost1.55/libboost-thread1.55.0_1.55.0+dfsg-3_amd64.deb
dpkg -i libboost-thread1.55.0_1.55.0+dfsg-3_amd64.deb
apt install libdb5.3++
apt install libminiupnpc10
wget http://ftp.us.debian.org/debian/pool/main/o/openssl/libssl1.0.0_1.0.1t-1+deb8u8_amd64.deb
dpkg -i libssl1.0.0_1.0.1t-1+deb8u8_amd64.deb
# Download the daemon
wget https://pandacoin.tech/files/pandacoind
