import sys
import configparser
import argparse
import contextlib
import json
import datetime
from collections import namedtuple

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


def download(conf):
    app = Client('pldump', conf['api_id'], conf['api_hash'])
    messages = []
    with app:
        for m in app.iter_history(conf['channel_name']):
            if m.text:
                text, tags = parse_message(m.text, m.entities)
                messages.append(Message(
                    id=m.message_id,
                    author=m.author_signature,
                    date=datetime.datetime.fromtimestamp(m.date),
                    text=text,
                    tags=tags
                ))
    return messages


def dump_markdown(messages):
    for m in messages:
        message_str = (
            f'{m.text}\n'
            '\n'
            f'{m.tags}\n'
            '\n'
            f'{m.author + ", " if m.author else ""}{m.date}\n'
        )
        print(message_str)


def dump_json(messages):
    # NOTE: convoluted as to covert namedtuples to json dicts we need to call
    # the _asdict method instead of serializing the whole message list
    m_strs = []
    for m in messages:
        def datetime_serializer(f):
            if isinstance(f, datetime.datetime):
                return f.isoformat()
        m_str = json.dumps(m._asdict(), default=datetime_serializer,
                           sort_keys=True, indent=4, ensure_ascii=False)
        m_strs.append(m_str)
    print('[\n' + ',\n'.join(m_strs) + '\n]')


DUMPERS = {
    'markdown': dump_markdown,
    'json': dump_json,
}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Download PLComp notes using the Telegrap API'
    )
    parser.add_argument('--config', default='plcomp.ini',
                        type=argparse.FileType('r', encoding='utf-8'))
    parser.add_argument('--output', default=sys.stdout,
                        type=argparse.FileType('w', encoding='utf-8'))
    parser.add_argument('--output-type', default='markdown',
                        choices=DUMPERS.keys())
    args = parser.parse_args()

    conf = configparser.ConfigParser()
    conf.read_file(args.config)

    messages = download(conf['dump'])
    dumper = DUMPERS[args.output_type]
    with contextlib.redirect_stdout(args.output):
        dumper(messages)
