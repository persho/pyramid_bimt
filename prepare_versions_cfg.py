import pkg_resources
version = pkg_resources.require('pyramid_bimt')[0].version

import os
os.rename('buildout.d/versions.cfg', 'versions-{}.cfg'.format(version))

