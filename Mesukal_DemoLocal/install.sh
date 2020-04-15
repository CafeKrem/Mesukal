
sudo apt update
sudo apt upgrade

sudo apt-get install tshark
sudo apt-get install vlc
sudo apt-get install wmctrl
sudo apt install python3-pip
sudo apt install python3-tk

##### pip3 install
pip3 install pathlib
pip3 install pandas
pip3 install matplotlib
pip3 install psutil
pip3 install tkinter
pip3 install --pre scapy
pip3 install argparse
 

# update a youtube.luac
cd /usr/lib/x86_64-linux-gnu/vlc/lua/playlist/
sudo rm youtube*
sudo wget https://raw.githubusercontent.com/videolan/vlc/master/share/lua/playlist/youtube.lua
