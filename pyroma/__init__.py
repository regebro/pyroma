import sys
import os
from pyroma import projectdata, distributiondata, pypidata, ratings

import logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format="%(message)s")

def zester(data):
    from zest.releaser.utils import ask
    if ask("Run pyroma on the package before uploading?"):
        result = run(data['workingdir'])
        if result != 10:
            if not ask("Continue?"):
                sys.exit(1)


def run(argument):
    logging.info('-'*30)
    logging.info('Checking ' + argument)
    
    if os.path.isdir(argument):
        data = projectdata.get_data(os.path.abspath(argument))
        logging.info('Found ' + data.get('name', 'nothing'))
    
    elif os.path.isfile(argument):
        data = distributiondata.get_data(os.path.abspath(argument))
        logging.info('Found ' + data.get('name', 'nothing'))
        
    else:
        # It's probably a package name
        data = pypidata.get_data(argument)
        logging.info('Found ' + data.get('name', 'nothing'))
    rating = ratings.rate(data)
        
    logging.info('-'*30)
    for problem in rating[1]:
        # XXX It would be nice with a * pointlist instead, but that requires
        # that we know how wide the terminal is and nice word-breaks, so that's
        # for later.
        logging.info(problem)
    if rating[1]:
        logging.info('-'*30)
    logging.info('Final rating: ' + str(rating[0]) + '/10')
    logging.info(ratings.LEVELS[rating[0]])
    logging.info('-'*30)
    return rating[0]


def main():
    if len(sys.argv) < 2:
        logging.info("Usage: pyroma <project directory|file|project name>")
        sys.exit(1)

    run(sys.argv[1])
