#BTech Project Repository

##Setup Instructions
Ensure that Python 2.7+ and virtualenv(https://virtualenv.readthedocs.org/
) are installed on your system.

1. Download modified copy of mitmproxy - `git clone https://github.com/anantk17/mitmproxy.git`
2. Download netlib - `git clone https://github.com/mitmproxy/netlib.git`
3. Download libpathod - `git clone https://github.com/mitmproxy/pathod.git`
4. Download Project Code - `git clone (https://github.com/anantk17/hashed-mango-kandies.git`
5. Move into the mitmproxy folder - `cd mitmproxy`
6. Create virtual environment and build files - `./dev`
7. Activate the virtual environment - `. ../venv.mitmproxy/bin/activate`
8. To run the test script (within the virtual environment) - `mitmproxy -s <path to local copy of hashed-mango-kandies>/testCode/script.py` 
