#!/usr/bin/python

# cPanel Metrics python plugin
# For more information see https://collectd.org/documentation/manpages/collectd-python.5.shtml

import sys
import time
import os
import mmap
from collections import Counter
import subprocess

try:
    import collectd
    import logging

    logging.basicConfig(level=logging.INFO)
except ImportError:
    try:
        import dummy_collectd as collectd
    except:
        pass

PLUGIN_NAME = 'cpanel'
FREQUENCY = 1.0
DATAPOINT_COUNT = 0
NOTIFICATION_COUNT = 0
PLUGIN_INSTANCE = "cpanel[frequency=%s]"
SEND = False
USERS_BLACKLIST = ["system"]


def log(param):
    """
    Log messages to either collectd or stdout depending on how it was called.

    :param param: the message
    :return:  None
    """

    if __name__ != '__main__':
        collectd.info("%s: %s" % (PLUGIN_NAME, param))
    else:
        sys.stderr.write("%s\n" % param)


def config(conf):
    """
    This method has been registered as the config callback and is used to parse options from
    given config.  Note that you cannot receive the whole config files this way, only Module blocks
    inside the Python configuration block. Additionally you will only receive blocks where your
    callback identifier matches your plugin.

    In this case Frequency is a float value that will modify the frequency of the sine wave. This
    in conjunction with the polling interval can give you as smooth or blocky a curve as you want.

    :param conf: a Config object
    :return: None
    """

    for kv in conf.children:
        if kv.key == 'Frequency':
            global FREQUENCY
            FREQUENCY = float(kv.values[0])


def read():
    """
    This method has been registered as the read callback and will be called every polling interval
    to dispatch metrics.  We emit three metrics: one gauge, a sine wave; two counters for the
    number of datapoints and notifications we've seen.

    :return: None
    """

    active_users = getActiveUsersCount()
    suspended_users = getSuspendedUsersCount()
    total_users = active_users + suspended_users
    plans = getPlans()
    version = getVersion()
    domains = getDomains()
    bandwidth = getBandwidth()


    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="active_users",
                    type="gauge",
                    values=[active_users]).dispatch()

    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="suspended_users",
                    type="gauge",
                    values=[suspended_users]).dispatch()

    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="total_users",
                    type="gauge",
                    values=[total_users]).dispatch()

    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="domains",
                    type="gauge",
                    values=[domains]).dispatch()

    for plan in plans.items():
        collectd.Values(plugin=PLUGIN_NAME,
                        type_instance="plans",
                        plugin_instance = plan[0],
                        type="gauge",
                        values=[plan[1]]).dispatch()

    for user in bandwidth.items():
        collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="bandwidth",
                    plugin_instance = user[0],
                    type="gauge",
                    values=[user[1]]).dispatch()
    
    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="version",
                    plugin_instance = version,
                    type="gauge",
                    values=[1]).dispatch()

    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="datapoints",
                    type="counter",
                    values=[DATAPOINT_COUNT]).dispatch()

    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="notifications",
                    type="counter",
                    values=[NOTIFICATION_COUNT]).dispatch()

    global SEND
    if SEND:
        notif = collectd.Notification(plugin=PLUGIN_NAME,
                                      type_instance="started",
                                      type="objects")  # need a valid type for notification
        notif.severity = 4  # OKAY
        notif.message = "The %s plugin has just started" % PLUGIN_NAME
        notif.dispatch()
        SEND = False


def init():
    """
    This method has been registered as the init callback; this gives the plugin a way to do startup
    actions.  We'll just log a message.

    :return: None
    """

    log("Plugin %s initializing..." % PLUGIN_NAME)


def shutdown():
    """
    This method has been registered as the shutdown callback. this gives the plugin a way to clean
    up after itself before shutting down.  We'll just log a message.

    :return: None
    """

    log("Plugin %s shutting down..." % PLUGIN_NAME)


def write(values):
    """
    This method has been registered as the write callback. Let's count the number of datapoints
    and emit that as a metric.

    :param values: Values object for datapoint
    :return: None
    """

    global DATAPOINT_COUNT
    DATAPOINT_COUNT += len(values.values)


def flush(timeout, identifier):
    """
    This method has been registered as the flush callback.  Log the two params it is given.

    :param timeout: indicates that only data older than timeout seconds is to be flushed
    :param identifier: specifies which values are to be flushed
    :return: None
    """

    log("Plugin %s flushing timeout %s and identifier %s" % PLUGIN_NAME, timeout, identifier)


def log_cb(severity, message):
    """
    This method has been registered as the log callback. Don't emit log messages from within this
    as you will cause a loop.

    :param severity: an integer and small for important messages and high for less important messages
    :param message: a string without a newline at the end
    :return: None
    """

    pass


def notification(notif):
    """
    This method has been regstered as the notification callback. Let's count the notifications
    we receive and emit that as a metric.

    :param notif: a Notification object.
    :return: None
    """

    global NOTIFICATION_COUNT
    NOTIFICATION_COUNT += 1

def getFilesInDir(path):
    """
    This method takes a file system path and returns a list of files and total count of files in the path
    :param path: a file system path
    :return: List, Integer
    """

    dir_list = os.listdir(path)
    output = []
    for item in dir_list:
        if os.path.isfile(os.path.join(path, item)):
            output.append(item)

    return output, len(output)

def matchFilesLine(path, file_name, line, inverted=False):
    """
    This method takes a file system path and a filename and a string to search for, it also takes an option boolean keyword 'inverted', if set it 
    will return True if the string is NOT found.

    """

    file_path = path + '/' + file_name
    try:
        with open(file_path) as f:
            s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            if not inverted:
                if s.find(line) != -1:
                    return True
                else:
                    return False
            else:
                if s.find(line) == -1:
                    return True
                else:
                    return False
    except ValueError:
        return False

def getActiveUsersCount():
    path = "/var/cpanel/users"
    all_users_list, all_users_count = getFilesInDir(path)

    active_users = 0
    for user in all_users_list:
        if matchFilesLine(path, user, 'SUSPENDED=1', inverted=True) and not user in USERS_BLACKLIST:
            active_users += 1
    return active_users

def getSuspendedUsersCount():
    path = "/var/cpanel/users"
    all_users_list, all_users_count = getFilesInDir(path)

    suspended_users = 0
    for user in all_users_list:
        if matchFilesLine(path, user, 'SUSPENDED=1', inverted=False) and not user in USERS_BLACKLIST:
            suspended_users += 1
    return suspended_users

def getPlans():
    path = "/var/cpanel/users"
    all_users_list, _ = getFilesInDir(path)
    plans = []
    for user in all_users_list:
        file_path = path + '/' + user
        try:
            with open(file_path) as f:
                s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                position = s.find('PLAN=')
                if position:
                    # We found a line matching PLAN=
                    s.seek(position)
                    line = s.readline()
                    plan = line.split('=')[1].strip('\n')
                    plans.append(plan)

        except ValueError:
            pass
    return Counter(plans)

def getBandwidth():
    path = "/var/cpanel/bandwidth.cache/"
    all_users_list, _ = getFilesInDir(path)
    bw = {}
    for user in all_users_list:
        if not user in USERS_BLACKLIST:
            file_path = path + '/' + user
            try:
                with open(file_path) as f:
                    s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                    bw_string = s.readline()
                    bw_int = int(bw_string)
                    bw[user] = bw_int
            except ValueError:
                pass
    return bw

def getVersion():
    command = '/usr/local/cpanel/cpanel -V'
    result,error  = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if not error:
        return result
    return 'Unknown'

def getDomains():
    path='/etc/userdomains'
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        return len(lines) - 1
    except ValueError:
        return 0

if __name__ != "__main__":
    # when running inside plugin register each callback
    collectd.register_config(config)
    collectd.register_read(read)
    collectd.register_init(init)
    collectd.register_shutdown(shutdown)
    collectd.register_write(write)
    # collectd.register_flush(flush)
    collectd.register_log(log_cb)
    collectd.register_notification(notification)
else:
    # outside plugin just collect the info
    read()
    if len(sys.argv) < 2:
        while True:
            time.sleep(10)
            read()