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
    # The ast module is buggy when it comes to handling comments and 
    # whitespace at the end of files. Whitespace we can strip:
    data = open(path, 'rt').read().strip()
    try:
        rootnode = ast.parse(data, filename=path)
    except SyntaxError, e:
        print "Warning could not parse a Python file. This is probably not your fault"
        print "File:", e.args[1][0]
        print "Line:", e.args[1][1]
        print "Code:", e.args[1][3]
        raise StopIteration
    
    for node in ast.walk(rootnode):
        if isinstance(node, ast.Import):
            for name in node.names:
                dependency = name.name
        elif isinstance(node, ast.ImportFrom):
            dependency = node.module
        else:
            continue

        if '.' in dependency:
            # Only the first name is relevant
            yield dependency.split('.')[0]
        else:
            yield dependency
    
def _find_py_modules(path):
    """Find all python files in the package in 'path'"""
    files = os.listdir(path)
    if '__init__.py' not in files:
        # This is not a part of the package
        raise StopIteration
    for filename in files:
        filepath = os.path.join(path, filename)
        if filename.endswith('.py'):
            # Yield the module name and the file path to the module.
            if filename == '__init__.py':
                yield filepath.split(os.path.sep)[-2], filepath
            else:
                yield os.path.splitext(filename)[0], filepath
        elif os.path.isdir(filepath):
            for x in _find_py_modules(filepath):
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

    # This didn't work well enough, maybe remove?
    ## Find all dependencies:
    #imports = set()
    #modules_in_package = set()
    #packages = metadata['packages']
    
    ## Remove namespace packages, for example):
    #for package in sorted(metadata['packages'], key=lambda x: -len(x)):
        #if '.' in package:
            #parent = package.rsplit('.', 1)[0]
            #if parent in packages:
                #packages.remove(package)
    
    #for package in packages:
        #if '.' in package:
            #package = package.replace('.', os.path.sep)
        #package_dirs = metadata.get('package_dir', {'':''})
        #package_dir = package_dirs.get(package, package_dirs[''])
            
        #for module, filepath in _find_py_modules(
            #os.path.join(path, package_dir, package)):
            #modules_in_package.add(module)
            #imports.update(list(_find_imports(filepath)))
                
    #metadata['_imports'] = imports - modules_in_package
    return metadata
    