from mcstatus import JavaServer
import logging

try :
    # You can pass the same address you'd enter into the address field in minecraft into the 'lookup' function
    # If you know the host and port, you may skip this and use JavaServer("example.org", 1234)
    server = JavaServer.lookup("dewcraft.duckdns.org:25565")

    # 'status' is supported by all Minecraft servers that are version 1.7 or higher.
    # Don't expect the player list to always be complete, because many servers run
    # plugins that hide this information or limit the number of players returned or even
    # alter this list to contain fake players for purposes of having a custom message here.
    status = server.status()
    print(f"The server has {status.players.online} player(s) online and replied in {status.latency} ms")

    # 'ping' is supported by all Minecraft servers that are version 1.7 or higher.
    # It is included in a 'status' call, but is also exposed separate if you do not require the additional info.
    latency = server.ping()
    print(f"The server replied in {latency} ms")

    # 'query' has to be enabled in a server's server.properties file!
    # It may give more information than a ping, such as a full player list or mod information.
    query = server.query()
    print(f"The server has the following players online: {', '.join(query.players.names)}")
except Exception as e:
    logging.error(e)