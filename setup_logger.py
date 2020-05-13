#setup_logginf

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('sim_log')
logger.addHandler(logging.FileHandler('test.log', 'a'))
print = logger.info