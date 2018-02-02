import smtplib, subprocess
from email.mime.text import MIMEText

def sendMail(fromadd, toadd, subj, msg, smtp='phys.nthu.edu.tw', port=25):
    mess = MIMEText(msg)
    mess['Subject'] = subj
    mess['From'] = fromadd
    mess['To'] = toadd
    s = smtplib.SMTP(smtp, port)
    s.sendmail(fromadd, [toadd], mess.as_string())
    s.quit()

def run_mollie(dirname, logger=None, shell='csh', np=1, server=None, mpi='mpiexec'):
    if shell=='csh':
        order = r"""csh -c 'cd %s; ps -A >>running.txt; make; %s -n %i ./c.x'"""
    else:
        order = r"""cd %s; make; %s -n %i c.x"""
    if logger:
        logger.info('Running: %s', order % (dirname, mpi, np))
    if server:
        logger.info('Connecting to: %s', server)
        subp = subprocess.Popen(['ssh', server, order % (dirname,mpi,np)],
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE)
    else:
        subp = subprocess.Popen(order % (dirname,mpi,np),
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE,
                                shell=True)
    mollie_stdout, mollie_stderr = subp.communicate()
    if logger:
        logger.info('Mollie standard output:\n%s', mollie_stdout)
        logger.info('Mollie standard error:\n%s', mollie_stderr)
