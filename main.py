import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

secret_role="Electric"

bot = commands.Bot(command_prefix='#', intents=intents)

@bot.event
async def on_ready():
    print(f'Started! {bot.user.name}')

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome {member.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if 'wow' in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention} WOOOOOOOW")

    await bot.process_commands(message)

@bot.command()
async def grafic(ctx):
    await ctx.send(f"Grafic today: {ctx.author.mention}")

@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now {secret_role}")
    else:
        await ctx.send(f"{ctx.author.mention} nema takogo")

bot.run(token, log_handler=handler, log_level=logging.DEBUG) 
