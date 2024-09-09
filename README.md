## Deluge-DDos
Python script to set up a denial of service attack on HTTP services (L7). \
The script is capable of sending up to 1000 requests per second. \
The number of requests sent depends mainly on the quality of the network connectivity of the site and the attacking machine.

The script allows:
- to use a random user-agent
- to use different HTTP headers for each request
- to use a proxy
- to change the HTTP method for each request (GET, POST, etc...)
