import os
import re
import sys
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
        sys.path.remove(self._old_path)
        os.chdir(self._path)
        
        if self._path not in sys.path:
            sys.path.append(self._path)
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

def _find_imports(path):
    contents = open(path, 'rt').read()
    for match in IMPORTS.findall(contents):
        for modules in match:
            if not modules:
                # Shortcut for the common '' case.
                continue
            # Handle import foo as bar
            if 'as' in modules:
                modules, ignore = modules.split('as', 1)
            # "import sys, os" needs a split into "sys", "os":
            modules = [x.strip() for x in modules.split(',')]
            for module in modules:
                # If modules are like "foo.bar" only "foo" is relevant.
                if '.' in module:
                    module, ignore = module.split('.')
                yield module

def _find_py_files(path):
    """Find all python files in the package in 'path'"""
    files = os.listdir(path)
    if '__init__.py' not in files:
        # This is not a part of the package
        raise StopIteration
    for filename in files:
        filepath = os.path.join(path, filename)
        if filename.endswith('.py'):
            yield filepath
        elif os.path.isdir(filepath):
            for x in _find_py_files(filepath):
                    yield x
    
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
        
    # Find all dependencies:
    imports = set()
    for package in metadata['packages']:
        for filepath in _find_py_files(os.path.join(path, package)):
            imports.update(list(_find_imports(filepath)))
                
    metadata['_imports'] = imports
    return metadata
    