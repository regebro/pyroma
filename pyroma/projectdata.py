# Extracts information from a project that has a distutils setup.py file.

import os
import re
import sys
#import ast
from collections import defaultdict

IMPORTS = re.compile('^import (.*)$|^from (.*?) import .*$', re.MULTILINE)

class SetupMonkey(object):
    
    def __init__(self, path):
        self._path = path
    
    def setup_replacement(self, **kw):
        self._kw = kw
        
    def get_data(self):
        return self._kw
        
    def __enter__(self):
        import distutils.core
        self._distutils_setup = distutils.core.setup
        distutils.core.setup = self.setup_replacement
        
        try:
            import setuptools
            self._setuptools_setup = setuptools.setup
            setuptools.setup = self.setup_replacement
        except ImportError:
            self._setuptools_setup = None

        self._old_path = os.path.abspath(os.curdir)
        if self._old_path in sys.path:
            sys.path.remove(self._old_path)
        os.chdir(self._path)
        
        if self._path not in sys.path:
            sys.path.insert(0, self._path)
            self._path_appended = True
        else:    
            self._path_appended = False
            
        return self
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        import distutils.core
        distutils.core.setup = self._distutils_setup
        if self._setuptools_setup is not None:
            import setuptools
            setuptools.setup = self._setuptools_setup
            
        if self._path_appended:
            sys.path.remove(self._path)
        sys.path.append(self._old_path)
        
        os.chdir(self._old_path)
    
def get_data(path):
    """
    Returns data from a package directory. 
    'path' should be an absolute path.
    """
    # Run the imported setup to get the metadata.
    with SetupMonkey(path) as sm:
        try:
            import setup
            metadata = sm.get_data()
            del sys.modules['setup']
        except ImportError:
            return {}

    return metadata
    