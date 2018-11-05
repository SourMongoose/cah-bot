# cards-against-humanity
Repository for the @cards-against-humanity Discord bot.  
You can add the bot to your server and view a list of commands here:  
https://discordbots.org/bot/429024440060215296

# Self Hosted
```
mkdir src/
cd src/
wget https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tgz
./configure --prefix=/home/${USER}/src/Python36/
make && make install
sudo apt-get install python-virtualenv
cd ~
virtualenv -p /home/${USER}/src/Python36/bin/python3.6 cahbot-env
source /home/${USER}/cahbot-env/bin/activate
cd ~/src/
git clone https://github.com/SourMongoose/cah-bot.git
git clone https://github.com/zalando-stups/python-tokens.git
cd python-tokens/
python setup.py install
cd -
git clone https://github.com/bspkrs/Cardcast-Python-API.git
cd Cardcast-Python-API
python setup.py install
cd -
pip install discord.py aiosqlite
# Should be at ${USER}/src/
cd cah-bot/src
python cahbot1.py
```
