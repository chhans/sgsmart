# Notice

This is a draft for integrating an SG smart gateway into home assistant. I just needed a way to switch on/off the lights, not have a fully working integration. B/c of this, it's just thrown together quickly. I am not going to support this officially. If you want to build something out of this, this should save you some time reverse engineering the communication. Send me a message if you do decide to complete this.

## Remaining work

From analyzing the traffic, it's necessary to send the following websocket messages to get the status of all SG smart devices connected to a gateway:

```
42["login", 10059, "{{username}}", "{{password}}", "android", "com.sgas.leddimapp", "4.34.785", "en"]
```

```
42["enterRoom",58468,"s_{{sector_uuid}}"]
```

The server should send messages with all the devices status at this point, which the integration must parse. The messages look like this:

```
42["extModelMessage",{{mesh_id}},65283,"23BC0138010000"]
``´

Where 23BC0138010000 can be decoded to something such as:

* `23BC01`: header
* `38`: brightness (56% in this example)
* `01`: on/off
* `0000`: sometimes this is not 0000, but I don't know what it means :)