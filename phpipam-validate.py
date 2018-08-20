#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" phpipam-validate.py: Script to validate phpIPAM installation """

__author__ = "Misha Komarovskiy <zombah@gmail.com>"
__copyright__ = "Copyright 2018"
__license__ = "GPL v3"
__version__ = "0.1"

import sys
import os
import git
import platform
import subprocess
import pymysql.cursors
import pymysql
import logging

# Global variables
LOGFORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOGLEVEL = logging.ERROR
logging.basicConfig(level=LOGLEVEL, format=LOGFORMAT)
config = 'config.php'


def git_repo(path):
    """ Check folder is git tracked repo """

    try:
        git.Repo(path).git_dir
        return True
    except Exception as e:
        logging.debug('%s' % repr(e))
        return False


def check_git_modules(path):
    """ Check that all git modules installed """

    try:
        git.Repo(path).submodules
        return True
    except Exception as e:
        logging.error('%s' % repr(e))
        return False


def has_uncommited(path):
    """ Check git repo dirty or not """

    dirty = git.Repo(path).is_dirty(index=True, working_tree=True,
                                    untracked_files=True, submodules=True)
    return dirty


def subproc(cmd):
    """ Run subprocess command """

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1,
                                universal_newlines=True)
        script_response = proc.stdout.readline()
        striped = script_response.rstrip()
        proc.stdout.close()
        return striped
    except Exception as e:
        logging.error('%s' % repr(e))


def matchline(strfile, value):
    """ Open file and search for specific line """

    with open(strfile) as f:
        for line in f:
            if value in line:
                return line


def getvalue(line):
    """ Get value of key value pair """

    words = line.split("\'")
    val = words[3]
    logging.debug('%s' % val)
    return val


def dbconnect(hostval, userval, paswval, nameval):
    """ Connect and select from MySQL db """

    try:
        dictcursor = pymysql.cursors.DictCursor
        mydb = pymysql.connect(db=nameval, host=hostval, user=userval,
                               passwd=paswval, cursorclass=dictcursor)
        cursor = mydb.cursor()
        sql = ("SELECT `%s`, `%s` FROM `%s`" % ('version', 'dbversion',
                                                'settings'))
        cursor.execute(sql)
        result = cursor.fetchone()
        mydb.close()
        logging.debug('%s' % result)
        return result
    except Exception as e:
        logging.error('%s' % repr(e))
        return None


# Header
print('phpipam-validate \n'
      '-------------------')
# Check python first
python = platform.python_version()
print('Python version: %s' % (python))

# Git check part
path = os.getcwd()
logging.debug('Current folder: %s' % path)

if git_repo(path) is True:
    repo = git.Repo(path)
    sha = repo.head.object.hexsha
    short_sha = repo.git.rev_parse(sha, short=9)
    branch = repo.active_branch.name
    untracked = has_uncommited(path)

    print('Git branch: %s, short-sha: %s, is dirty: %s' % (branch, short_sha,
                                                           untracked))
    if check_git_modules(path) is True:
        print('Git modules installed fine.')
    else:
        logging.error('Git modules error.')

else:
    print('Not git tracked folder')

# System check part
linux = platform.linux_distribution()
arch = platform.machine()

print('Linux: %s, version: %s, optional: %s' % (linux[0], linux[1], linux[2]))
print('System arch: %s' % (arch))

# PHP and MySQL checks
php_version = subproc(['php', '--version'])
mysql_version = subproc(['mysql', '--version'])

print('PHP: %s' % (php_version))
print('MySQL: %s' % (mysql_version))

# Config file check
check_config = os.path.isfile(config)
if check_config is True:
    precheck = True
    print('Config file %s exist' % (config))
else:
    precheck = False
    logging.error('No config file %s' % config)


# Parse config for mysql schema version check
dbhost = '''$db['host']'''
dbuser = '''$db['user']'''
dbpass = '''$db['pass']'''
dbname = '''$db['name']'''


if precheck is True:
    host = matchline(config, dbhost)
    user = matchline(config, dbuser)
    pasw = matchline(config, dbpass)
    name = matchline(config, dbname)
    hostvalue = getvalue(host)
    uservalue = getvalue(user)
    paswvalue = getvalue(pasw)
    namevalue = getvalue(name)

    dbversion = dbconnect(hostvalue, uservalue, paswvalue, namevalue)
    if dbversion is not None:
        print('DB Version: %s, Schema version: %s' % (dbversion["version"],
                                                      dbversion["dbversion"]))


sys.exit('-------------------\n'
         'Check finished.')
