#!/usr/bin/python

'''
Speeds are in bps
'''

import datetime
import pytz
import urllib, httplib
import urllib2
import getopt, sys
from time import time
import random
from threading import Thread, currentThread
from math import pow, sqrt
import bisect
import re

###############

HOST = 'speedtest-po.vodafone.pt'
RUNS = 2
VERBOSE = 0
HTTPDEBUG = 0

STORM_ACCESS_TOKEN = 'YOUR ACCESS TOKEN'
STORM_PROJECT_ID = 'YOUR PROJECT ID'
STORM_SOURCETYPE = 'syslog'

###############

DOWNLOAD_FILES = [
    '/speedtest/random350x350.jpg',
    '/speedtest/random500x500.jpg',
    '/speedtest/random1500x1500.jpg',
    ]

UPLOAD_FILES = [
    132884,
    493638
]

class StormLog(object):
    """A simple example class to send logs to a Splunk Storm project.

    Your ``access_token`` and ``project_id`` are available from the Storm UI.
    """

    def __init__(self, access_token, project_id, input_url=None):
        self.url = input_url or 'https://api.splunkstorm.com/1/inputs/http'
        self.project_id = project_id
        self.access_token = access_token

        self.pass_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        self.pass_manager.add_password(None, self.url, 'x', access_token)
        self.auth_handler = urllib2.HTTPBasicAuthHandler(self.pass_manager)
        self.opener = urllib2.build_opener(self.auth_handler)
        urllib2.install_opener(self.opener)

    def send(self, event_text, sourcetype='syslog', host=None, source=None):
        params = {'project': self.project_id,
                  'sourcetype': sourcetype}
        if host:
            params['host'] = host
        if source:
            params['source'] = source
        url = '%s?%s' % (self.url, urllib.urlencode(params))
        try:
            req = urllib2.Request(url, event_text)
            response = urllib2.urlopen(req)
            return response.read()
        except (IOError, OSError), ex:
            # An error occured during URL opening or reading
            raise



def printv(msg):
    if VERBOSE : print msg

def downloadthread(connection, url):
    connection.request('GET', url, None, { 'Connection': 'Keep-Alive'})
    response = connection.getresponse()
    self_thread = currentThread()
    self_thread.downloaded = len(response.read())

def download():
    total_downloaded = 0
    connections = []
    for run in range(RUNS):
        connection = httplib.HTTPConnection(HOST)
        connection.set_debuglevel(HTTPDEBUG)
        connection.connect()
        connections.append(connection)
    total_start_time = time()
    for current_file in DOWNLOAD_FILES:
        threads = []
        for run in range(RUNS):
            thread = Thread(target = downloadthread, args = (connections[run], current_file + '?x=' + str(int(time() * 1000))))
            thread.run_number = run
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
            total_downloaded += thread.downloaded
            printv('Run %d for %s finished' % (thread.run_number, current_file))
    total_ms = (time() - total_start_time) * 1000
    for connection in connections:
        connection.close()
    printv('Took %d ms to download %d bytes' % (total_ms, total_downloaded))
    return (total_downloaded * 8000 / total_ms)

def uploadthread(connection, data):
    url = '/speedtest/upload.php?x=' + str(random.random())
    connection.request('POST', url, data, {'Connection': 'Keep-Alive', 'Content-Type': 'application/x-www-form-urlencoded'})
    response = connection.getresponse()
    reply = response.read()
    self_thread = currentThread()
    self_thread.uploaded = int(reply.split('=')[1])

def upload():
    connections = []
    for run in range(RUNS):
        connection = httplib.HTTPConnection(HOST)
        connection.set_debuglevel(HTTPDEBUG)
        connection.connect()
        connections.append(connection)

    post_data = []
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for current_file_size in UPLOAD_FILES:
        values = {'content0' : ''.join(random.choice(ALPHABET) for i in range(current_file_size)) }
        post_data.append(urllib.urlencode(values))

    total_uploaded = 0
    total_start_time = time()
    for data in post_data:
        threads = []
        for run in range(RUNS):
            thread = Thread(target = uploadthread, args = (connections[run], data))
            thread.run_number = run
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
            printv('Run %d for %d bytes finished' % (thread.run_number, thread.uploaded))
            total_uploaded += thread.uploaded
    total_ms = (time() - total_start_time) * 1000
    for connection in connections:
        connection.close()
    printv('Took %d ms to upload %d bytes' % (total_ms, total_uploaded))
    return (total_uploaded * 8000 / total_ms)

def ping(server):
    connection = httplib.HTTPConnection(server)
    connection.set_debuglevel(HTTPDEBUG)
    connection.connect()
    times = []
    worst = 0
    for i in range(5):
        total_start_time = time()
        connection.request('GET', '/speedtest/latency.txt?x=' + str(random.random()), None, { 'Connection': 'Keep-Alive'})
        response = connection.getresponse()
        response.read()
        total_ms = time() - total_start_time
        times.append(total_ms)
        if total_ms > worst:
            worst = total_ms
    times.remove(worst)
    total_ms = sum(times) * 250 # * 1000 / number of tries (4) = 250
    connection.close()
    printv('Latency for %s - %d' % (server, total_ms))
    return total_ms

def chooseserver():
    connection = httplib.HTTPConnection('www.speedtest.net')
    connection.set_debuglevel(HTTPDEBUG)
    connection.connect()
    now = int(time() * 1000)
    extra_headers = {
        'Connection': 'Keep-Alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
        }
    connection.request('GET', '/speedtest-config.php?x=' + str(now), None, extra_headers)
    response = connection.getresponse()
    reply = response.read()
    m = re.search('<client ip="([^"]*)" lat="([^"]*)" lon="([^"]*)"',reply)
    location = None
    if m == None:
        printv("Failed to retrieve coordinates")
        return None
    location = m.groups()
    printv('Your IP: %s\nYour latitude: %s\nYour longitude: %s' % location)
    connection.request('GET', '/speedtest-servers.php?x=' + str(now), None, extra_headers)
    response = connection.getresponse()
    reply = response.read()
    server_list = re.findall('<server url="([^"]*)" lat="([^"]*)" lon="([^"]*)"', reply)
    my_lat = float(location[1])
    my_lon = float(location[2])
    sorted_server_list = []
    for server in server_list:
        s_lat = float(server[1])
        s_lon = float(server[2])
        distance = sqrt(pow(s_lat - my_lat,2) + pow(s_lon - my_lon, 2))
        bisect.insort_left(sorted_server_list,(distance, server[0], s_lat, s_lon))
    best_server = (999999, '')
    for server in sorted_server_list[:10]:
        printv(server[1])
        m = re.search('http://([^/]+)/speedtest/upload\.php',server[1])
        if not m : continue
        server_host = m.groups()[0]
        latency = ping(server_host)
        server_lat = server[2]
        server_lon = server[3]
        if latency < best_server[0]:
            best_server = (latency, server_host, server_lat, server_lon)
    printv('Best server: ' + best_server[1])
    distance = best_server[0]
    server_location = (best_server[2], best_server[3])
    return best_server[1], location, server_location, distance

def usage():
    print '''
usage: pyspeedtest.py [-h] [-v] [-r N] [-m M] [-d L]

Test your bandwidth speed using Speedtest.net servers.

optional arguments:
 -h, --help         show this help message and exit
 -v                 enabled verbose mode
 -r N, --runs=N     use N runs (default is 2).
 -m M, --mode=M     test mode: 1 - download, 2 - upload, 4 - ping, 1 + 2 + 4 = 7 - all (default).
 -d L, --debug=L    set httpconnection debug level (default is 0).
 -s                 find best server
'''

def main():
    global VERBOSE, RUNS, HTTPDEBUG, HOST
    mode = 7
    findserver = True
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hr:vm:d:s", ["help", "runs=","mode=","debug="])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o == "-v":
            VERBOSE = 1
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-r", "--runs"):
            try:
                RUNS = int(a)
            except ValueError:
                print 'Bad runs value'
                sys.exit(2)
        elif o in ("-m", "--mode"):
            try:
                mode = int(a)
            except ValueError:
                print 'Bad mode value'
                sys.exit(2)
        elif o in ("-d", "--debug"):
            try:
                HTTPDEBUG = int(a)
            except ValueError:
                print 'Bad debug value'
                sys.exit(2)
        elif o == "-s":
            findserver = True

    if findserver:
        HOST, my_location, server_location, distance = chooseserver()
        my_ip = my_location[0]
        my_lat = my_location[1]
        my_lon = my_location[2]
        server_lat = server_location[0]
        server_lon = server_location[1]
    if mode & 4 == 4:
        my_ping = ping(HOST)
        printv('Ping: %d ms' % ping(HOST))
    if mode & 1 == 1:
        my_download = download()
        printv('Download speed: ' + pretty_speed(download()))
    if mode & 2 == 2:
        my_upload = upload()
        printv('Upload speed: ' + pretty_speed(upload()))
    timestamp = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat()
    logline = (
        "%s host=%s, my_lat=%s, my_lon=%s, testserver=%s, lat=%s, lon=%s, "
        "distance_to_server=%0.2f, ping=%d, download=%0.2f, upload=%0.2f"
        % (timestamp, my_ip, my_lat, my_lon, HOST, server_lat, server_lon,
           distance, my_ping, my_download, my_upload))
    print logline

    log = StormLog(STORM_ACCESS_TOKEN, STORM_PROJECT_ID)
    log.send(logline, sourcetype=STORM_SOURCETYPE)

def pretty_speed(speed):
    units = [ 'bps', 'Kbps', 'Mbps', 'Gbps' ]
    unit = 0
    while speed >= 1024:
        speed /= 1024
        unit += 1
    return '%0.2f %s' % (speed, units[unit])

if __name__ == '__main__':
    main()