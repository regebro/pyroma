import os
import re

from collections import defaultdict

try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

CLASSIFIER_URL = "https://pypi.org/pypi?%3Aaction=list_classifiers"
CLASSIFIER_FILE = "pyroma/classifiers.py"
SHORT_NAME_RE = re.compile(br"\(.*?\)")


def update_classifiers():
    source = urlopen(CLASSIFIER_URL).read()
    classifiers = [each.strip() for each in source.splitlines()]
    licenses = [each for each in classifiers if each.startswith(b"License")]
    license_map = defaultdict(set)
    code_map = defaultdict(set)
    for license in licenses:
        short_name = SHORT_NAME_RE.findall(license)
        if short_name:
            short_name = short_name[0][1:-1]
            code_map[short_name].add(license)
            license_map[license].add(short_name)
            if short_name.startswith(b"GPL"):
                code_map[b"GPL"].add(license)
                license_map[license].add(b"GPL")
            elif short_name.startswith(b"LGPL"):
                code_map[b"LGPL"].add(license)
                license_map[license].add(b"LGPL")
        elif b"Zope" in license:
            code_map[b"ZPL"].add(license)
            license_map[license].add(b"ZPL")
        elif b"MIT License" in license:
            code_map[b"MIT"].add(license)
            license_map[license].add(b"MIT")

    with open(CLASSIFIER_FILE, "wb") as out:
        out.write(b"""CLASSIFIERS = {\n""")
        for classifier in classifiers:
            out.write(b'    "%s",\n' % classifier)
        out.write(b"""}\n\n""")

        out.write(b"""LICENSE_CODES = {\n""")
        for license, codes in license_map.items():
            out.write(b'    "%s": {"' % license)
            out.write(b'", "'.join(codes))
            out.write(b'"},\n')
        out.write(b"""}\n\n""")

        out.write(b"""CODE_LICENSES = {\n""")
        for code, licenses in code_map.items():
            out.write(b'    "%s": {\n        "' % code)
            out.write(b'",\n        "'.join(licenses))
            out.write(b'"},\n')
        out.write(b"""}\n\n""")


if __name__ == "__main__":
    # Verify that we are in the right directory
    if not os.path.exists(CLASSIFIER_FILE):
        raise RuntimeError(
            "You must run this script from the root directory of " "a Pyroma checkout."
        )
    update_classifiers()
