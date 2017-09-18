# delete ENTRY files older than a week
import os, sys
import datetime


def cleanup(forreal=False, verbose=False):
    filesdir = os.path.join(os.getcwd(), 'losttime', 'static', 'userfiles')
    deleted = 0
    for filename in os.listdir(filesdir):
        if filename.startswith('EntryForOE-') or filename.startswith('EntryForCheckIn-'):
            fullpath = os.path.join(filesdir, filename)
            file_timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(fullpath))
            a_week_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7))
            if file_timestamp < a_week_ago:
                if forreal:
                    os.remove(fullpath)
                if verbose:
                    print('Deleted: {}'.format(filename))
                deleted += 1
    if forreal and verbose:
        print('Deleted {} files'.format(deleted))
    elif verbose:
        print('Could have deleted {} files'.format(deleted))
    return deleted if forreal else 0

if __name__ == '__main__':
    forreal = True if 'doit' in sys.argv else False
    verbose = True if 'talk' in sys.argv else False
    if 'help' in sys.argv or '-h' in sys.argv:
        print('Usage: python file_cleanup.py <args>')
        print('doit: include to actually delete files')
        print('talk: include for verbose output')
    else:
        cleanup(forreal, verbose)