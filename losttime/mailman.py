from subprocess import Popen, PIPE
from losttime import app


def send_email(sender, recipient, subject, body, verbose=False):
    if verbose:
        print('Sending {} to {}'.format(subject, recipient))

    header = "From: {0}\nTo: {1}\nSubject: {2}\n".format(sender, recipient, subject)
    header += "MIME-Version: 1.0\nContent-Type: text/html\n\n"
    message = header + body

    if app.config["SEND_EMAILS"]:
        p = Popen(['/usr/bin/sendmail', "-t"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        res = p.communicate(message)
    else:
        res = message

    if verbose:
        print('Process completed with: {}\n'.format(res))
    return res