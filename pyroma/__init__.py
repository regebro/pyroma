import os
import sys
from optparse import OptionParser
from pyroma import projectdata, distributiondata, pypidata, ratings

import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format="%(message)s")


def zester(data):
    main_files = os.listdir(data["workingdir"])
    if "setup.py" not in main_files and "setup.cfg" not in main_files:
        return

    from zest.releaser.utils import ask

    if ask("Run pyroma on the package before tagging?"):
        rating = run("directory", os.path.abspath(data["workingdir"]))
        if rating < 8:
            if not ask("Continue?"):
                sys.exit(1)


def main():
    usage = (
        "usage: %prog [-n N] [-a|-d|-f|-p] <project directory|"
        "distribution file|pypi package name>"
    )
    parser = OptionParser(usage)
    parser.add_option(
        "-n",
        "--min",
        dest="min",
        default=8,
        action="store",
        type=int,
        help="Minimum rating for clean return between 0 and 10, inclusive",
    )
    parser.add_option(
        "-a",
        "--auto",
        dest="auto",
        default=False,
        action="store_true",
        help="Select mode automatically (default)",
    )
    parser.add_option(
        "-d",
        "--directory",
        dest="directory",
        action="store_true",
        default=False,
        help="Run pyroma on a module in a project directory",
    )
    parser.add_option(
        "-f",
        "--file",
        dest="file",
        action="store_true",
        default=False,
        help="Run pyroma on a distribution file",
    )
    parser.add_option(
        "-p",
        "--pypi",
        dest="pypi",
        action="store_true",
        default=False,
        help="Run pyroma on a package on PyPI",
    )

    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    if not (0 <= options.min <= 10):
        parser.print_help()
        sys.exit(1)

    modes = (options.auto, options.directory, options.file, options.pypi)
    if sum([1 if x else 0 for x in modes]) > 1:
        print("You can only select one of the options -a, -d, -f and -p")
        sys.exit(1)

    argument = args[0]

    mode = "pypi"
    if not any(modes) or options.auto:
        if os.path.isdir(argument):
            mode = "directory"
        elif os.path.isfile(argument):
            mode = "file"
    elif options.directory:
        mode = "directory"
    elif options.file:
        mode = "file"

    rating = run(mode, argument)
    if rating < options.min:
        sys.exit(2)
    sys.exit(0)


def run(mode, argument):

    logging.info("-" * 30)
    logging.info("Checking " + argument)

    if mode == "directory":
        data = projectdata.get_data(os.path.abspath(argument))
        logging.info("Found " + data.get("name", "nothing"))
    elif mode == "file":
        data = distributiondata.get_data(os.path.abspath(argument))
        logging.info("Found " + data.get("name", "nothing"))
    else:
        # It's probably a package name
        data = pypidata.get_data(argument)
        logging.info("Found " + data.get("name", "nothing"))

    rating = ratings.rate(data)

    logging.info("-" * 30)
    for problem in rating[1]:
        # XXX It would be nice with a * pointlist instead, but that requires
        # that we know how wide the terminal is and nice word-breaks, so that's
        # for later.
        logging.info(problem)
    if rating[1]:
        logging.info("-" * 30)
    logging.info("Final rating: " + str(rating[0]) + "/10")
    logging.info(ratings.LEVELS[rating[0]])
    logging.info("-" * 30)

    return rating[0]
