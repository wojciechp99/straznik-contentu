from datetime import datetime
import json
import math
import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.guild_messages = True
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_message(message):
    guild = discord.utils.get(client.guilds, name=GUILD)
    channel = message.channel
    if message.content.startswith('$content'):
        await channel.send(f'Dawać Content! @everyone')

    elif message.content.startswith('$roles'):
        with open('roles.json', 'r', encoding='utf-8') as json_file:
            roles = json.load(json_file)
            json_file.close()
        await channel.send("Na serwerze jest do zdobycia 10 możliwych rang za dawanie contentu:\n")
        for index, role in enumerate(roles):
            await channel.send(f"{index + 1}. {role['name']} - Wymaga dawania minimum {role['hours']}h contentu\n")

    elif message.content.startswith('$myStats'):
        path = f'users/{message.author.name}.json'
        if os.path.exists(path):
            with open(path, 'r') as json_file:
                user = json.load(json_file)
                json_file.close()
            await channel.send(f"Ranga: {guild.get_role(user['role']).name}\nCzas contentu: {math.floor(user['hours'])}h")
        else:
            await channel.send('Niestety nie posiadam twoim danych, co oznacza, że NIE DAWAŁEŚ/AŚ CONTENTU!!')

    elif message.content.startswith('Wojtek sra'):
        await channel.send(f"{message.author.name} sra")

    elif message.content.startswith('$help'):
        await channel.send("""
            Komendy Straźnika Contentu:\n
            $content -> uprzejmnie prosi o content\n
            $roles   -> pokazuję rangi i ich wymagania\n
            $myStats -> pokazuję rolę i ile godzin dawało się content
        """)


@client.event
async def on_voice_state_update(member, before, after):
    if before.self_stream is False and after.self_stream is True:
        await update_user_json(member, datetime.now().strftime('%d/%m/%Y %H:%M:%S.%f'), None)
    elif before.self_stream is True and after.self_stream is False:
        await update_user_json(member, None, datetime.now().strftime('%d/%m/%Y %H:%M:%S.%f'))


async def update_user_json(member, stream_start, stream_end):
    path = f'users/{member.name}.json'
    if os.path.exists(path):
        await update_user(path=path, member=member, stream_start=stream_start, stream_end=stream_end)
    else:
        await create_user(path=path, member=member, stream_start=stream_start, stream_end=stream_end)


async def update_user(path, member, stream_start, stream_end):
    with open(path, 'r', encoding='utf-8') as json_file:
        user = json.load(json_file)
        json_file.close()
    updated_user = user
    if stream_start:
        updated_user['stream_start'] = str(stream_start)
        updated_user['stream_end'] = None
    if stream_end and updated_user['stream_start']:
        updated_user['stream_end'] = str(stream_end)
        hours = count_hours(updated_user['stream_start'], updated_user['stream_end'])
        updated_user['hours'] += hours

        new_role = await update_role_id(member, updated_user['hours'], updated_user['role'])

        updated_user['stream_start'] = None
        updated_user['stream_end'] = None
        updated_user['role'] = new_role

    with open(path, 'w', encoding='utf-8') as final_json_file:
        json.dump(updated_user, final_json_file, indent=4)


def count_hours(start, end):
    if start is None or end is None:
        return 0
    diff = datetime.strptime(end, '%d/%m/%Y %H:%M:%S.%f') - datetime.strptime(start, '%d/%m/%Y %H:%M:%S.%f')
    return diff.seconds / 3600


async def create_user(path, member, stream_start, stream_end):
    guild = discord.utils.get(client.guilds, name=GUILD)
    new_user = {
        "id": member.id,
        "name": member.name,
        "role": 1134104704683626626,
        "stream_start": str(stream_start),
        "stream_end": str(stream_end),
        "hours": 0
    }
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(new_user, json_file, indent=4)
    await member.add_roles(guild.get_role(1134104704683626626), reason="RANK ADDED")


async def update_role_id(member, user_hours, user_current_role):
    guild = discord.utils.get(client.guilds, name=GUILD)
    with open('roles.json', 'r', encoding='utf-8') as json_file:
        roles = json.load(json_file)
        json_file.close()
    # TODO update roles json by adding last role with hours: "inf"
    if user_hours > 5000:
        # gives last role
        if user_current_role != roles[9]['id']:
            await member.add_roles(guild.get_role(roles[9]['id']), reason="RANK LEVEL UP")
            await member.remove_roles(guild.get_role(user_current_role), reason="RANK LEVEL UP")

    new_user_role = user_current_role
    for index, _ in enumerate(roles):
        if roles[index]['hours'] < user_hours < roles[index + 1]['hours']:
            if user_current_role != roles[index]['id']:
                new_user_role = roles[index]['id']
                await member.remove_roles(guild.get_role(user_current_role), reason="RANK LEVEL UP")
        else:
            await member.remove_roles(guild.get_role(roles[index]['id']))
    await member.add_roles(guild.get_role(new_user_role))
    return new_user_role


@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name=GUILD)
    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )


client.run(TOKEN)
