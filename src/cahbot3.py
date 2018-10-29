import discord

from shard import Shard

client = discord.Client(shard_id=3, shard_count=4)

@client.event
async def on_ready():
    await s.on_ready()

@client.event
async def on_message(message):
    await s.on_message(message)

@client.event
async def on_reaction_add(reaction, user):
    await s.on_reaction_add(reaction, user)

s = Shard(3, client)
s.run()
