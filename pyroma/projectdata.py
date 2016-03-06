# Extracts information from a project that has a distutils setup.py file.
import os
import sys
import logging

from copy import copy
from distutils import core

# From six (where else?):
if sys.version_info[0] == 3:
    def exec_(_code_, _globs_=None, _locs_=None):
        exec(_code_, _globs_, _locs_)
else:
    def exec_(_code_, _globs_=None, _locs_=None):
        """Execute code in a namespace."""
        if _globs_ is None:
            frame = sys._getframe(1)
            _globs_ = frame.f_globals
            if _locs_ is None:
                _locs_ = frame.f_locals
            del frame
        elif _locs_ is None:
            _locs_ = _globs_
        exec("""exec _code_ in _globs_, _locs_""")


class FakeContext(object):

    def __init__(self, path):
        self._path = path

    def __enter__(self):
        self._old_path = os.path.abspath(os.curdir)
        if self._old_path in sys.path:
            sys.path.remove(self._old_path)
        os.chdir(self._path)

        if self._path not in sys.path:
            sys.path.insert(0, self._path)
            self._path_appended = True
        else:
            self._path_appended = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._path_appended:
            sys.path.remove(self._path)
        sys.path.append(self._old_path)

        os.chdir(self._old_path)


class SetupMonkey(object):

    used_setuptools = False

    def distutils_setup_replacement(self, **kw):
        self._distutils_setup(**kw)

    def setuptools_setup_replacement(self, **kw):
        self.used_setuptools = True
        self._setuptools_setup(**kw)

    def get_data(self):
        return self._kw

    def __enter__(self):
        import distutils.core
        self._distutils_setup = distutils.core.setup
        distutils.core.setup = self.distutils_setup_replacement

        try:
            import setuptools
            self._setuptools_setup = setuptools.setup
            setuptools.setup = self.setuptools_setup_replacement
        except ImportError:
            self._setuptools_setup = None

        self._kw = {}
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import distutils.core
        distutils.core.setup = self._distutils_setup
        if self._setuptools_setup is not None:
            import setuptools
            setuptools.setup = self._setuptools_setup


# This is a version of distutils run_setup() that doesn't give
# up just because Setuptools throws errors if you try to exec it.
def run_setup(script_name, script_args=None, stop_after="run"):
    """Run a setup script in a somewhat controlled environment, and
    return the Distribution instance that drives things.  This is useful
    if you need to find out the distribution meta-data (passed as
    keyword args from 'script' to 'setup()', or the contents of the
    config files or command-line.

    'script_name' is a file that will be run with 'execfile()';
    'sys.argv[0]' will be replaced with 'script' for the duration of the
    call.  'script_args' is a list of strings; if supplied,
    'sys.argv[1:]' will be replaced by 'script_args' for the duration of
    the call.

    'stop_after' tells 'setup()' when to stop processing; possible
    values:
      init
        stop after the Distribution instance has been created and
        populated with the keyword arguments to 'setup()'
      config
        stop after config files have been parsed (and their data
        stored in the Distribution instance)
      commandline
        stop after the command-line ('sys.argv[1:]' or 'script_args')
        have been parsed (and the data stored in the Distribution)
      run [default]
        stop after all commands have been run (the same as if 'setup()'
        had been called in the usual way

    Returns the Distribution instance, which provides all information
    used to drive the Distutils.
    """
    if stop_after not in ('init', 'config', 'commandline', 'run'):
        raise ValueError("invalid value for 'stop_after': %r" % stop_after)

    core._setup_stop_after = stop_after

    save_argv = sys.argv
    glocals = copy(globals())
    glocals['__file__'] = script_name
    glocals['__name__'] = "__main__"
    try:
        try:
            sys.argv[0] = script_name
            if script_args is not None:
                sys.argv[1:] = script_args
            f = open(script_name)
            try:
                exec_(f.read(), glocals, glocals)
            finally:
                f.close()
        finally:
            sys.argv = save_argv
            core._setup_stop_after = None
    except Exception:
        logging.warn("Exception when running setup.", exc_info=True)

    if core._setup_distribution is None:
        raise RuntimeError(
            "'distutils.core.setup()' was never called -- "
            "perhaps '%s' is not a Distutils setup script?" %
            script_name)

    # I wonder if the setup script's namespace -- g and l -- would be of
    # any interest to callers?
    return core._setup_distribution


def get_data(path):
    """
    Returns data from a package directory.
    'path' should be an absolute path.
    """
    # Run the imported setup to get the metadata.
    with FakeContext(path):
        with SetupMonkey() as sm:
            try:
                distro = run_setup('setup.py', stop_after='config')

                metadata = {'_setuptools': sm.used_setuptools}

                for k, v in distro.metadata.__dict__.items():
                    if k[0] == '_' or not v:
                        continue
                    if all(not x for x in v):
                        continue
                    metadata[k] = v

                if sm.used_setuptools:
                    for extras in ['cmdclass', 'zip_safe', 'test_suite']:
                        v = getattr(distro, extras, None)
                        if v is not None and v not in ([], {}):
                            metadata[extras] = v

            except ImportError as e:
                # Either there is no setup py, or it's broken.
                logging.exception(e)
                metadata = {}

    return metadata
