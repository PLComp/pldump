import json
import configparser
from pathlib import Path
from telethon import TelegramClient
from telethon.tl import types
from collections import namedtuple

Message = namedtuple('Message', 'id author date text tags')


def fix_entity(text):
    return text.replace('\n', '') + '\n' if '\n' in text else text


def parse_entity(entity, data):
    if isinstance(entity, types.MessageEntityBold):
        return fix_entity(f'**{data}**')
    elif isinstance(entity, types.MessageEntityItalic):
        return fix_entity(f'*{data}*')
    elif isinstance(entity, types.MessageEntityUrl):
        return fix_entity(f'[{data}]({data})')
    elif isinstance(entity, types.MessageEntityTextUrl):
        return fix_entity(f'[{data}]({entity.url})')
    elif isinstance(entity, types.MessageEntityCode):
        return f'`{data}`'
    elif isinstance(entity, types.MessageEntityPre):
        return f'<pre>{data}</pre>'
    return ''


def parse_text(text, entities):
    entities = sorted(entities, key=lambda e: e.offset)
    result = []
    pos = 0
    for e in entities:
        result.append(text[pos:e.offset])
        result.append(parse_entity(e, text[e.offset:e.offset + e.length]))
        pos = e.offset + e.length
    result.append(text[pos:])
    return ''.join(result).strip()


def parse_tags(text):
    last_line = text.strip().split('\n').pop()
    if last_line.startswith('#'):
        return [tag[1:] for tag in last_line.split() if tag.startswith('#')]
    return []


def pldump(conf):
    client = TelegramClient(conf['channel_name'],
                            conf['api_id'], conf['api_hash'])
    messages = []

    async def task():
        group = await client.get_entity(conf['channel_url'])
        async for m in client.iter_messages(group):
            if m.message:
                messages.append(Message(
                    id=m.id,
                    author=m.post_author,
                    date=(m.date.year, m.date.month, m.date.day),
                    text=parse_text(m.message, m.entities),
                    tags=parse_tags(m.message)
                ))
    with client:
        client.loop.run_until_complete(task())
    return messages


if __name__ == '__main__':
    conf = configparser.ConfigParser()
    conf.read('plcomp.ini')
    messages = pldump(conf['dump'])
    for m in messages:
        print(m.author, m.date, m.tags)
        print(m.text)
        print()
