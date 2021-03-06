from __future__ import print_function

import os
import re
import time

g_cache = {}
g_expire_time = 0

def cache_users(logFunction=print):
    """ Cache the entries in the variuos local-users.txt files
        Those entries are saved in a global variable with this
        format:

        {'username1': set(['T3_IT_Bologna']),
         'username2': set(['T2_US_Nebraska']),
         'username3': set(['T2_ES_CIEMAT', 'T3_IT_Bologna']),
         'userdn1': set(['T2_ES_CIEMAT']),
         'userfqan: set(['T2_ES_CIEMAT', 'T3_IT_Bologna'])
    """
    global g_expire_time
    global g_cache

    base_dir = '/cvmfs/cms.cern.ch/SITECONF'
    cache = {}
    user_re = re.compile(r'[-_A-Za-z0-9.]+')
    sites = None
    try:
        if os.path.isdir(base_dir):
            sites = os.listdir(base_dir)
    except OSError as ose:
        logFunction("Cannot list SITECONF directories in cvmfs:" + str(ose))
    if not sites:
        g_expire_time = time.time() + 60
        return
    for entry in sites:
        full_path = os.path.join(base_dir, entry, 'GlideinConfig', 'local-users.txt')
        if (entry == 'local') or (not os.path.isfile(full_path)):
            continue
        try:
            fd = open(full_path)
            for line in fd:
                line = line.strip()
                if user_re.match(line):
                    group_set = cache.setdefault(line, set())
                    group_set.add(entry)
        except OSError as ose:
            logFunction("Cannot list SITECONF directories in cvmfs:" + str(ose))
            raise


    g_cache = cache
    g_expire_time = time.time() + 15*60


def map_user_to_groups(user):
    """ Get the sites where user, userdn and userfqan
        are present as local-users and return them

        The list of sites is returned as a set of strings
    """
    if time.time() > g_expire_time:
        cache_users()
    return g_cache.setdefault(user, set([]))

if __name__ == '__main__':
   print(map_user_to_groups("bbockelm"))

