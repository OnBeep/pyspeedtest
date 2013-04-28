pyspeedtest
==========
Originally was just a python script to test network bandwidth using
Speedtest.net servers. Now it does that but logs to Splunk Storm (as well
as print to stdout) with increased information.

You'll need to first sign up for a free project at http://www.splunkstorm.com
Then under the API tab on the Inputs page for your project you'll find the
Access token and Project ID to fill in at the top of the script.

In most cases, this should be run without parameters in order to do a full test
of ping, download speed, and upload speed. Speeds are returned in bps, while
ping is obviously returned in seconds.

Recommended usage is via cronjob:

    */20 * * * * /usr/bin/python /path/to/pyspeedtest/pyspeedtest.py

If you want to log locally as well:

    */20 * * * * /usr/bin/python /path/to/pyspeedtest/pyspeedtest.py >> /path/to/logs/speedtest.log
