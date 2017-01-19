#!/usr/bin/env python
# encoding: utf-8

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
