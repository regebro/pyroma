# Extracts information from a project that has a distutils setup.py file.
import build
import build.util
import logging
import os
import pathlib
import sys
import tokenize
from copy import copy
from distutils import core

try:  # config renamed to config.setupcfg on Setuptools >=61 adding pyproject.toml support
    from setuptools.config.setupcfg import read_configuration
except ModuleNotFoundError:
    from setuptools.config import read_configuration

METADATA_MAP = {
    "summary": "description",
    "classifier": "classifiers",
    "project_url": "project_urls",
    "home_page": "url",
    "description": "long_description",
    "description_content_type": "long_description_content_type",
    "requires_python": "python_requires",
}


def build_metadata(path, isolated=None):
    # If explictly specified whether to use isolation, pass it directly
    if isolated is not None:
        return build.util.project_wheel_metadata(path, isolated=isolated)

    # Otherwise, try without build isolation first for efficiency
    try:
        return build.util.project_wheel_metadata(path, isolated=False)
    # If building with build isolation fails, e.g. missing build deps, try with it
    except build.BuildBackendException:
        return build.util.project_wheel_metadata(path, isolated=True)


def map_metadata_keys(metadata):
    data = {}
    if "Description" not in metadata.keys():
        # Having the description as a payload tends to add two newlines, we clean that up here:
        long_description = metadata.get_payload().strip() + "\n"
        data["long_description"] = long_description

    for key in set(metadata.keys()):
        value = metadata.get_all(key)
        if len(value) == 1:
            value = value[0]
            if value.strip() == "UNKNOWN":
                continue
        key = key.lower().replace("-", "_")
        if key in METADATA_MAP:
            key = METADATA_MAP[key]
        data[key] = value
    return data


def get_build_data(path, isolated=None):
    metadata = build_metadata(path, isolated=isolated)
    return map_metadata_keys(metadata)


def get_setupcfg_data(path):
    # Note: By default, setup.cfg will read the pyroma.git/setup.cfg - forcing explicit setup.cfg under test's file path
    data = read_configuration(str(pathlib.Path(path) / "setup.cfg"))
    metadata = data["metadata"]
    return metadata


def get_data(path):
    data = _get_data(path)
    data["_path"] = path
    return data


def _get_data(path):
    try:
        return get_build_data(path)
    except build.BuildException as e:
        if "no pyproject.toml or setup.py" in e.args[0]:
            # It couldn't build the package, because there is no setup.py or pyproject.toml.
            # Let's see if there is a setup.cfg:
            try:
                metadata = get_setupcfg_data(path)
                # Yes, there's a setup.cfg. Pyroma accepted this earlier, but that was probably
                # a mistake. For the time being, warn for it, but in a future version just fail.
                metadata["_missing_build_system"] = True
                return metadata
            except Exception:
                # No, that didn't work. Hide this second exception and raise the first:
                pass
        raise e

    except Exception:
        logging.exception("Exception raised during metadata preparation")
        metadata = get_setuppy_data(path)
        metadata["_stoneage_setuppy"] = True
        return metadata


class FakeContext:
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


class SetupMonkey:
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
    if stop_after not in ("init", "config", "commandline", "run"):
        raise ValueError(f"invalid value for 'stop_after': {stop_after!r}")

    core._setup_stop_after = stop_after

    save_argv = copy(sys.argv)
    glocals = copy(globals())
    glocals["__file__"] = script_name
    glocals["__name__"] = "__main__"
    try:
        try:
            sys.argv[0] = script_name
            if script_args is not None:
                sys.argv[1:] = script_args
            with tokenize.open(script_name) as f:
                exec(f.read(), glocals, glocals)
        finally:
            sys.argv = save_argv
            core._setup_stop_after = None
    except Exception:
        logging.warning("Exception when running setup.", exc_info=True)

    if core._setup_distribution is None:
        raise RuntimeError(
            f"'distutils.core.setup()' was never called -- perhaps '{script_name}' is not a Distutils setup script?"
        )

    # I wonder if the setup script's namespace -- g and l -- would be of
    # any interest to callers?
    return core._setup_distribution


def get_setuppy_data(path):
    """
    Returns data from a package directory.
    'path' should be an absolute path.
    """
    metadata = {}
    # Run the imported setup to get the metadata.
    with FakeContext(path):
        with SetupMonkey() as sm:
            if os.path.isfile("setup.py"):
                try:
                    distro = run_setup("setup.py", stop_after="config")

                    metadata = {}

                    for k, v in distro.metadata.__dict__.items():
                        if k[0] == "_" or not v:
                            continue
                        if all(not x for x in v):
                            continue
                        metadata[k] = v

                    if sm.used_setuptools:
                        for extras in ["cmdclass", "zip_safe", "test_suite"]:
                            v = getattr(distro, extras, None)
                            if v is not None and v not in ([], {}):
                                metadata[extras] = v
                except Exception as e:
                    # Looks like setup.py is broken.
                    logging.exception(e)
                    metadata = {}

            elif os.path.isfile("setup.cfg"):
                try:
                    data = read_configuration("setup.cfg")
                    metadata = data["metadata"]
                    metadata["_setuptools"] = True
                except Exception as e:
                    logging.exception(e)

            else:
                logging.exception("Neither setup.py nor setup.cfg was found")

    return metadata
