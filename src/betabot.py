import discord

from beta_shard import Shard

client = discord.AutoShardedClient()

@client.event
async def on_ready():
    await s.on_ready()

@client.event
async def on_message(message):
    await s.on_message(message)

@client.event
async def on_reaction_add(reaction, user):
    await s.on_reaction_add(reaction, user)

s = Shard(client)
s.run()
