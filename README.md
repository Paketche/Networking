# Networking
<h2>Included applications</h2>
<ul>
    <li>Ping clone</li>
    <li>Trace route clone</li>
    <li>Single-threaded HTTP server</li>
    <li>HTTP client</li>
    <li>Single-threaded HTTP proxy</li>
</ul>

<h3>Ping clone</h3>

<p>Constructs and sends ICMP echo messages to a configurable host. After each sent message it waits for a response and measures
    the round-trip time. After the specified number of pings have been sent. An average is calculated. This implementation
    uses a raw socket</p>

<h3>Trace round clone</h3>

<p>Uses the ping module to send individual ICMP echo messages and with every few messages, it increases their time to live. After
    each response a round-trip time is displayed and the IP address of the echoing node is displayed. After the destination
    has been reached it stops</p>

<h3>Single-threaded HTTP server</h3>

<p>Serves HTTP GET requests by replaying with either a 200 OK or 404 Not Found if the requested file does not exist. The server
    also handles conditional GET messages by serving content only if needed.</p>

<h3>Single-threaded HTTP proxy</h3>

<p>Serves cached content. If a page is not in the cache the proxy contacts the origin server for the content and saves it after
    relaying it to the client. The proxy stores the cache-control header information about the received content and before each serving it checks if the content is stale or not. If it is it send a conditional GET message to the origin server.
    If it receives new content it simply relays it to the client and saves it, otherwise, it serves the one on the cache.</p>
