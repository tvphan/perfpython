import requests
import os


def make_db(item):
    """
    Make the db, ignore if it already exists.
    """
    auth = ()
    if item.config.env['TESTY_SAVE_PASS'] and \
            item.config.env['TESTY_SAVE_USER']:

        auth = (
            item.config.env['TESTY_SAVE_USER'],
            item.config.env['TESTY_SAVE_USER']
        )

    requests.put(item.config.env.get('TESTY_SAVE_URL'), auth=auth,)


def delete_file_ignore_errors(path):
    """
    Attempts deletion of the specified path.
    Ignores any errors that might occur.
    """
    try:
        os.remove(path)
    except:
        pass
