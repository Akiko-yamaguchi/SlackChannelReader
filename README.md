# SlackChannelReader

Read messages of a channel and backup them!

# How to use

Read the messages from the channel.

```python
reader = SlackChannelReader(token, channel_id)
messages = reader.read()
```

Dump to JSON.

```python
serializer = MessageSerializer()
serializer.dump_json(messages, "dump.json")
```

Parse JSON file you have dumped.

```python
serializer = MessageSerializer()
serializer.parse_json("dump.json")
```

Dump to CSV.

```python
serializer = MessageSerializer()
serializer.dump_csv(msgs, "dump.csv")
```

# TODO

Enable serializing without existing data to be duplicated or be lost.
