import ConfigParser
import os


def get_adm_creds():
    """
    Return adm creds in a (user, password) tuple, as read from the
    user's Clou config file.
    """
    conf = ConfigParser.ConfigParser()
    conf.read(os.path.expanduser('~/.clou'))
    creds = (
        conf.get('cloudant', 'adm_user'),
        conf.get('cloudant', 'adm_password'),
    )
    return creds
