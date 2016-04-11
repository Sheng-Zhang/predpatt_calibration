#!/usr/bin/env python
# encoding: utf-8

import csv, json
import argparse
from predpatt.Predpattern import Predpattern, Argument
from predpatt import CommUtil
from converter import html_escape

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
                        help='path to the input file. Accepts Concrete communications and CoNLLU formats.')
    parser.add_argument('output',
                        help='output')
    parser.add_argument('-n', '--num', type=int, default=None,
                        help='The number of sents.')
    parser.add_argument('-f', '--format',
                        choices=('color', 'plain'), default='plain')
    parser.add_argument('-d', '--debug', default='')
    parser.add_argument('--simple', action='store_true')
    parser.add_argument('--cut', action='store_true')
    parser.add_argument('--track-rule', action='store_true')
    parser.add_argument('--show-deps', action='store_true')
    parser.add_argument('--show-deps-cols', type=int, default=4)
    parser.add_argument('--resolve-relcl', action='store_true',
                        help='Enable relative clause resolution rule.')
    parser.add_argument('--resolve-appos', action='store_true',
                        help='Enable apposition resolution rule.')
    parser.add_argument('--resolve-poss', action='store_true',
                        help='Enable possessive resolution rule.')
    parser.add_argument('--resolve-conj', action='store_true',
                        help='Enable conjuction resolution rule.')
    parser.add_argument('--resolve-amod', action='store_true',
                        help='Enable adjectival modifier resolution rule.')

    args = parser.parse_args()
    args.big_args = False

    return args

def extract_predpattern(sys_args):
    for slabel, parse in CommUtil.load_conllu(sys_args.filename):
        ppatt = Predpattern(parse, sys_args)
        if ppatt:
            yield slabel, parse, ppatt

def extract():
    sys_args = parse_args()
    f = open(sys_args.output, 'wb')
    writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
    writer.writerow(['json_variables'])
    row_i, row= 0, []
    for slabel, parse, ppatt in extract_predpattern(sys_args):
        if row_i > 10:
            break
        entails = {}
        entails['sentence'] = html_escape(' '.join([tk.text for tk in ppatt.tokens]))
        entails['sentenceID'] = slabel
        entail_i = 0
        for pred in ppatt.instances:
            item_list = []
            for item in sorted(pred.tokens+pred.arguments):
                if isinstance(item, Argument):
                    if (item.root.gov_rel in {'ccomp', 'csubj', 'xcomp'}
                        and item.root.gov in pred.tokens and pred.type == 'normal'):
                        break
                    elif item.root.tag in {'DET', 'PROP', 'DT', 'WDT', 'PDT', 'EX', 'PRP'}:
                        break
                    item_list.append(' '.join([tk.text for tk in item.tokens]))
                else:
                    item_list.append(item.text)
            else:
                item_list[0] = item_list[0][0].upper() + item_list[0][1:]
                entail_i += 1
                entail = html_escape(' '.join(item_list))
                entails['entail_'+str(entail_i)] = entail
        if len(entails) > 2:
            row.append(entails)
        if len(row) == 5:
            writer.writerow([json.dumps(row, sort_keys=True)])
            row_i += 1
            row = []
    f.close()


if __name__ == "__main__":
  extract()


