import json
import configparser
from pathlib import Path
from collections import namedtuple
from datetime import datetime
from pyrogram import Client

Message = namedtuple('Message', 'id author date text tags')


def fix_entity(text):
    return text.replace('\n', '') + '\n' if '\n' in text else text


def parse_entity(entity, data):
    if entity.type == 'bold':
        return fix_entity(f'**{data}**')
    elif entity.type == 'italic':
        return fix_entity(f'*{data}*')
    elif entity.type == 'url':
        return fix_entity(f'[{data}]({data})')
    elif entity.type == 'text_link':
        return fix_entity(f'[{data}]({entity.url})')
    elif entity.type == 'code':
        return f'`{data}`'
    elif entity.type == 'pre':
        return f'```\n{data.strip()}\n```\n'
    return data


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


def parse_message(text, entities):
    lines, tags = parse_text(text, entities).split('\n'), []
    last_line = lines[-1].strip()
    if last_line.startswith('#'):
        lines.pop()
        tags = [tag[1:] for tag in last_line.split() if tag.startswith('#')]
    return '\n'.join(lines), tags


def pldump(conf):
    app = Client('pldump', conf['api_id'], conf['api_hash'])
    messages = []
    with app:
        for m in app.iter_history(conf['channel_name']):
            if m.text:
                text, tags = parse_message(m.text, m.entities)
                messages.append(Message(
                    id=m.message_id,
                    author=m.author_signature,
                    date=datetime.fromtimestamp(m.date),
                    text=text,
                    tags=tags
                ))
    return messages


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    conf = configparser.ConfigParser()
    conf.read('plcomp.ini')
    messages = pldump(conf['dump'])
    for m in messages:
        print(f'#### {m.author}, {m.date}')
        print(m.text)
        print(m.tags)
