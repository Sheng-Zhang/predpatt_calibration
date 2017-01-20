#!/usr/bin/env python
# encoding: utf-8
import codecs
from predpatt.UDParse import DepTriple, UDParse

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    '`': "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    "-LRB-": '(',
    "-RRB-": ')'}

REPLACEMENTS = {'-LRB-': '(',
                '-RRB-': ')',
                '-LSB-': '[',
                '-RSB-': ']',
                '-LCB-': '{',
                '-RCB-': '}'}


def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c, c) for c in text)


def ptb2text(x):
    """Convert special PTB tokens back to normal.

    >>> ptb2text('three -LRB- 3 -RRB- .')
    'three ( 3 ) .'

    """
    return ' '.join(REPLACEMENTS.get(y, y) for y in x.split())


def load_conllu(filename):
    sent_num = 1
    with codecs.open(filename, encoding='utf-8') as f:
        for block in f.read().split('\n\n'):
            block = block.strip()
            if not block:
                continue
            lines = []
            sent_id = 'sent_%s' % sent_num
            has_sent_id = 0
            for line in block.split('\n'):
                if line.startswith('#'):
                    if line.startswith('# sent_id'):
                        sent_id = line[10:].strip()
                        has_sent_id = 1
                    else:
                        if not has_sent_id:   # don't take subsequent comments as sent_id
                            sent_id = line[1:].strip()
                    continue
                line = line.split('\t') # data appears to use '\t'
                if '-' in line[0]:      # skip multi-tokens, e.g., on Spanish UD bank
                    continue
                assert len(line) == 10, line
                lines.append(line)
            [_, tokens, _, tags, _, _, gov, gov_rel, _, _] = zip(*lines)
            triples = [DepTriple(rel, int(gov)-1, dep) for dep, (rel, gov) in enumerate(zip(gov_rel, gov))]
            parse = UDParse(list(tokens), tags, triples)
            yield sent_id, parse
            sent_num += 1

