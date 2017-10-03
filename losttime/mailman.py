from subprocess import Popen, PIPE
from losttime import app


def send_email(sender, recipient, subject, body, verbose=False):
    if verbose:
        print('Sending {} to {}'.format(subject, recipient))

    header = "From: {0}\nTo: {1}\nSubject: {2}\n\n".format(sender, recipient, subject)
    message = header + body

    if app.config["SEND_EMAILS"]:
        p = Popen(['/usr/sbin/sendmail', "-t"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        res = p.communicate(message)
    else:
        res = message

    if verbose:
        print('Process completed with {}'.format(res))
    return res


if __name__ == '__main__':
    print(send_email('bot@example.com', 'eric@ercjns.com', 'TestMail', 'This is a test message.', True))