import os
from numpy.distutils.core import setup

setup(
    name = "RMANAGER",
    version = "2.0",
    author = "Raphael Dussin",
    author_email = "raphael.dussin@gmail.com",
    description = ("Easy set-up and running of ocean models simulations " ),
    license = "GPLv3",
    keywords = "ocean simulations",
    url = "https://github.com/raphaeldussin/RMANAGER",
    packages=['RMANAGER'],
)

os.system('./postinstall.bash')
