import discord

from beta_shard import Shard

client = discord.Client(shard_id=1, shard_count=2)

@client.event
async def on_ready():
    await s.on_ready()

@client.event
async def on_message(message):
    await s.on_message(message)

@client.event
async def on_reaction_add(reaction, user):
    await s.on_reaction_add(reaction, user)

s = Shard(1, client, 2)
s.run()