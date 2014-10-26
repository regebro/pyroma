# Extracts information from a project that has a distutils setup.py file.
import os
import sys
import logging

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

    def distutils_setup_replacement(self, **kw):
        self._kw = kw
        self._kw['_setuptools'] = False

    def setuptools_setup_replacement(self, **kw):
        self._kw = kw
        self._kw['_setuptools'] = True

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


def _specified_versions(data):
    classifiers = data.get('classifiers', [])
    for classifier in classifiers:
        parts = [p.strip() for p in classifier.split('::')]
        if parts[0] == 'Programming Language' and parts[1] == 'Python':
            if len(parts) == 2:
                # Specified Python, but no version.
                continue
            version = parts[2]
            try:
                int(version)
                # This is just specifying 2 or 3, not which version
                continue
            except ValueError:
                pass
            try:
                float(version)
                # This version is good!
                yield version
            except ValueError:
                # Not a proper Python version
                continue

def get_data(path):
    """
    Returns data from a package directory.
    'path' should be an absolute path.
    """
    # Run the imported setup to get the metadata.
    with FakeContext(path):
        with SetupMonkey() as sm:
            try:
                import setup
                metadata = sm.get_data()

                if not metadata:
                    # This may be a module, like twisted, that only runs setup()
                    # when setup.py is called as the main script. In that case it
                    # often has a main() script to call instead. Try that.
                    try:
                        setup.main()
                    except TypeError: # OK, so it's twisted.
                        try:
                            setup.main([])
                        except TypeError:
                            pass # OK, not twisted, then.
                    except AttributeError:
                        pass # No, no main.

                    metadata = sm.get_data()
                del sys.modules['setup']
            except ImportError as e:
                # Either there is no setup py, or it's broken.
                logging.exception(e)
                metadata = {}

        # No data found
        if not metadata:
            return {}

    return metadata
