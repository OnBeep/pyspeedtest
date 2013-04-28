pyspeedtest
==========
Originally was just a python script to test network bandwidth using
Speedtest.net servers. Now it does that but logs to Splunk Storm (as well
as print to stdout) with increased information.

http://www.splunkstorm.com

In most cases, this should be run without parameters in order to do a full test
of ping, download speed, and upload speed. Speeds are returned in bps, while
ping is obviously returned in seconds.

Recommended usage is via cronjob:

    */20 * * * * /usr/bin/python /path/to/pyspeedtest/pyspeedtest.py

If you want to log locally as well:

    */20 * * * * /usr/bin/python /path/to/pyspeedtest/pyspeedtest.py >> /path/to/logs/speedtest.log
