from datetime import datetime
import csv
import asyncio
import dotenv
import os
import discord
from mcstatus import JavaServer
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict

dotenv.load_dotenv()

token = str(os.getenv("TOKEN"))
ip = str(os.getenv("IP"))
userid = str(os.getenv("USERID"))

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

server = JavaServer.lookup(ip)

startlog = False
player_online_times = defaultdict(int)

# add help, visualizer, convert more commands, and add more graph fields
#fields = ['Date', 'Time', 'Status', 'Ping', 'Version', 'Player Count', 'Player List', 'MOTD']

async def serverreq():
    try:
        ping = await server.async_ping()
    except:
        return False, False
    status = await server.async_status()
    return status, ping

async def log():        
    with open("log.csv", "a", newline='') as outfile:
        date = datetime.now().strftime('%m-%d-%y')
        time = datetime.now().strftime('%H:%M')
        status, ping = await serverreq()
        if status == False:
            row = [date, time, "Offline", "", "", "", "", "", ""]
            writer = csv.writer(outfile)
            writer.writerow(row)
            return
        version = status.version.name
        player_count = status.players.online
        player_list = status.players.sample
        if player_list is None:
            player_list_str = ""
        else:
            player_list_str = ",".join([player.name for player in player_list])
        motd = status.motd.to_plain()
        row = [date, time, "Online", ping, version, player_count, player_list_str, motd]
        writer = csv.writer(outfile)
        writer.writerow(row)

async def main():
    while startlog == True:
        await log()
        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$ping'):
        await message.channel.send('Pong!')

    if message.content.startswith('$log'):
        words = message.content.split()
        if len(words) >= 2:
            if str(message.author.id) == userid:
                argument = words[1]
                if argument == 'start':
                    global startlog
                    startlog = True
                    await message.channel.send('Started logging')
                    await main()                
                elif argument == 'stop':
                    startlog = False
                    await message.channel.send("Stopped logging")
                else:
                    await message.channel.send("Invalid argument. Use $help for more information.")
            else:
                await message.channel.send("You don't have permission to stop/start logging")
        else:
            await log()
            await message.channel.send('Logged')

    if message.content.startswith('$online'):
        online = (await serverreq())[1]
        if online == False:
            await message.channel.send('Server is offline')
        else:
            await message.channel.send(f'Server is online, ping is {online}ms from the bot to the server')
    
    if message.content.startswith('$version'):
        version = (await serverreq())[0].version.name
        await message.channel.send(f'The server is running {version}')

    if message.content.startswith('$players'):
        player_count = (await serverreq())[0].players.online
        player_list = (await serverreq())[0].players.sample
        if player_list is None:
            player_list_str = "None"
        else:
            player_list_str = ", ".join([player.name for player in player_list])
        await message.channel.send(f"There are {player_count} players online\nPlayers online: {player_list_str}")
    
    if message.content.startswith('$motd'):
        motd = (await serverreq())[0].motd.to_plain()
        await message.channel.send(f'The MOTD is: {motd}')
    
    if message.content.startswith('$graph'):
        words = message.content.split()
        if len(words) >= 2:
            argument = words[1]
            with open('log.csv', 'r') as logcsv:
                csv_reader = csv.DictReader(logcsv)
                player_online_times.clear()
                if argument == 'players':
                    for row in csv_reader:
                        player_list_str = row['Player List']
                        if player_list_str:
                            player_list = player_list_str.split(',')
                            for player in player_list:
                                player_online_times[player] += 1
                    players = list(player_online_times.keys())
                    online_times = list(player_online_times.values())
                    plt.bar(players, online_times)
                    plt.xlabel('Player')
                    plt.ylabel('Online Time (minutes)')
                    plt.title('Player Online Time Comparison')
                    plt.xticks(rotation=45, ha='right')
                    img_data = io.BytesIO()
                    plt.savefig(img_data, format='png', bbox_inches='tight')
                    img_data.seek(0)
                    img_base64 = base64.b64encode(img_data.read()).decode('utf-8')
                    file = discord.File(io.BytesIO(base64.b64decode(img_base64)), filename='plot.png')
                    await message.channel.send(file=file)
                    plt.clf()
                elif argument == 'version':
                    await message.channel.send('Not implemented yet')
                elif argument == 'motd':
                    await message.channel.send('Not implemented yet')
                else:
                    await message.channel.send('Invalid argument. Use $help for more information.')
        else:
            await message.channel.send('Requires argument. Use $help for more information.')
        
    if message.content.startswith('$help'):
        words = message.content.split()
        if len(words) >= 2:
            argument = words[1]
            if argument == 'log':
                embed = discord.Embed(title="Commands", description="Here is a list of all the $log arguments!", timestamp=datetime.now())
                embed.set_author(name="Minecraft Bot", url="https://github.com/bestadamdagoat")
                embed.add_field(name="start", value="Starts logging automatically. Must be an admin to run this argument.", inline=False)
                embed.add_field(name="stop", value="Stops logging automatically. Must be an admin to run this argument.", inline=False)
                embed.set_footer(text="BestAdam", icon_url="https://avatars.githubusercontent.com/u/66372881?v=4")
                await message.channel.send(embed=embed)
            elif argument == 'graph':
                embed = discord.Embed(title="Commands", description="Here is a list of all the $graph arguments!", timestamp=datetime.now())
                embed.set_author(name="Minecraft Bot", url="https://github.com/bestadamdagoat")
                embed.add_field(name="players", value="Shows a bar graph comparing the online time of each player.", inline=False)
                embed.set_footer(text="BestAdam", icon_url="https://avatars.githubusercontent.com/u/66372881?v=4")
                await message.channel.send(embed=embed)
        else:
            embed = discord.Embed(title="Commands", description="Here is a list of all the current commands!\n\n> Run $help (command) to view all arguments for a command", timestamp=datetime.now())
            embed.set_author(name="Minecraft Bot", url="https://github.com/bestadamdagoat")
            embed.add_field(name="$ping", value="Checks if the bot is online. If it is, you'll get a response with \"Pong!\"", inline=False)
            embed.add_field(name="$log", value="Logs the date and time of the log, the server status, server ping, server version, player count, player list, and MOTD manually. Has extra arguments.", inline=False)
            embed.add_field(name="$online", value="Checks if the server is online or offline. Ping is recorded from the server location, it's not your ping.", inline=False)
            embed.add_field(name="$version", value="Checks what version of Minecraft the server is running.", inline=False)
            embed.add_field(name="$players", value="Checks what and how many players are online.", inline=False)
            embed.add_field(name="$motd", value="Checks the server's MOTD.", inline=False)
            embed.add_field(name="$graph", value="Shows a graph of the server's statistics. Requires an argument.", inline=False)
            embed.set_footer(text="BestAdam", icon_url="https://avatars.githubusercontent.com/u/66372881?v=4")
            await message.channel.send(embed=embed)

client.run(token)