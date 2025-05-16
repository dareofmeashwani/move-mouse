pip3 install virtualenv
virtualenv -p python3.9 venv
source venv/bin/activate
pip3 install -r requirements-dev.txt
pip3 install -r requirements.txt
brew install python-tk