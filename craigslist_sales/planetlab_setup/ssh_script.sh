sudo yum install -y tinyproxy
sudo sh -c "echo 'Allow 73.222.245.0/24' >> /etc/tinyproxy/tinyproxy.conf"
sudo /etc/init.d/tinyproxy restart
