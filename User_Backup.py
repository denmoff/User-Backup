#!/usr/bin/python

############ User_Backup.py ########################################
#
# Created by Dennis Moffett
# May, 4 2015
# Rutgers University
# Version 1.0.1
# Purpose: To backup user data from Mac to network share
######################################################################

import subprocess, os, sys, getpass, time, commands, logging
from subprocess import Popen, PIPE, call

user_name = getpass.getuser()
comp_name = Popen(['/usr/sbin/scutil', '--get', 'ComputerName']\
    ,stdout=PIPE,shell=False).communicate()[0].split('\n')[0]
#comp_name = socket.gethostname().rsplit('.')[0]
source_path = os.path.join('/Users', user_name)+"/"
dest_path = os.path.join('/Volumes', user_name,'Backups')
backup_dir = os.path.join(dest_path, comp_name)
last_run_file = os.path.join(dest_path, "." + comp_name)
run_interval = 90 #minutes
#log_path = os.path.join(source_path,'Library', 'Logs','User_Backup.log')
log_path = os.path.join('/Users','Shared','User_Backup.log')


### If rsyc3 exsists, use it. Otherwise, use system rsync.
if os.path.isfile('/usr/local/bin/rsync3'):
    rsync = '/usr/bin/rsync'
    #rsync = '/usr/local/bin/rsync3'
else:
    rsync = '/usr/bin/rsync'

inclusions = ["Library/Mail/"]
exclusions = [".ssh",".Trash", ".cache", "Dropbox", "Downloads",\
 "Library", "Movies", "Music", "Pictures", "Documents/Microsoft User Data"]
filter_file = '/Users/Shared/.filter'



logging.basicConfig(filename=log_path,filemode='w',format='%(asctime)s:%(message)s',level=logging.DEBUG)
logging.debug(user_name)

def main():
    # x_string = create_exclude_string(exclusion_list)
    if flight_check():
        logging.info("Running backup...")
        rsync_command(source_path,backup_dir) 


def flight_check():
    go1 = os.path.isdir(backup_dir) # sets go1 to true if backup directory exists.
    if go1:
        logging.info("The Destination is: %s and it appears to be available. The Computername is: %s" % (dest_path,comp_name))
    else:
        logging.info("The Destination is: %s and it DOES NOT appear to be available. The Computername is: %s" % (dest_path,comp_name))
        logging.info("Attempting to create backup directory...")
        try:
            os.makedirs(backup_dir)
            if os.path.isdir(backup_dir):
                logging.info("Backup directory successfully created.")
                go1 = True
        except Exception:
            logging.info("Could not create backup directory.")
            logging.info("Exiting.")
            return False

    if os.path.isfile(last_run_file):
        if int((time.time() - os.path.getmtime(last_run_file))/60) > run_interval:# has it run in the last n minutes
            go2 = True
        else:
            go2 = False
            logging.info("Backup has run within the last %s minutes" % run_interval)
    else: # If Last Run File is missing, try to create it. If it fails, set go2 to False. If it succeeds, set to True.
        go2 = False
        logging.info("Missing the last run file. Will attempt to create it...")
        try:
            open(last_run_file, 'a').close()
            if os.path.isfile(last_run_file):
                logging.info("File successfully created.")
                go2 = True
        except Exception:
            logging.info("Could not create file.")

    if commands.getoutput('pgrep rsync') == '':
        go3 = True
    else:
        go3 = False
        logging.info("An instance of rsync is already running. Will try again shortly.")

    # logging.info("Backup directory exists: %s, a backup has not already run recently: %s, rsync is not currently running: %s" % (go1,go2,go3))
    
    if go1 and go2 and go3:
        return True
    else:
        return False    

def rsync_command(src,dst):
    rsync_args = [rsync,"-az", "--delete", "--force", src, dst]
    if not os.path.isfile(filter_file):# If there is no .filter file, use include/exclude lists (defined at top). Otherwise, use .filter file.
        for x in exclusions:
            rsync_args.insert(2, '--exclude=%s' % x)
        for i in inclusions:
            rsync_args.insert(2, '--include=%s' % i)
    else:
        rsync_args.insert(2, '--filter=merge %s' % filter_file)
    
    rp = Popen(rsync_args,stdout=PIPE,stderr=PIPE,shell=False)
    rsync_stdout,rsync_stderr = rp.communicate()
    logging.debug(rsync_stdout)
    logging.info("Rsync Complete.")
    os.utime(last_run_file,None)

if __name__ == "__main__":
    main()
