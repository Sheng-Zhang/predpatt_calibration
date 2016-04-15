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

def highlight_sentence(sent_tokens, pred, colors):
    def highlight(tokens, color):
        if len(tokens) == 0:
            return None
        last_index = -1
        for tk in tokens:
            index = tk.position
            text = sent_tokens[index]
            if last_index == -1:
                sent_tokens[index] = '<span style=\\"background-color:%s\\">%s'%(color, text)
            else:
                span = index - last_index
                if span != 1:
                    sent_tokens[last_index] += '</span>'
                    sent_tokens[index] = '<span style=\\"background-color:%s\\">%s'%(color, text)
            last_index = index
        sent_tokens[last_index] += '</span>'

    if pred.type != 'poss':
        highlight(pred.tokens, colors['pred'])
    for arg_i, arg in enumerate(sorted(pred.arguments)):
        arg_i = arg_i%len(colors['arg'])
        highlight(arg.tokens, colors['arg'][arg_i])

    return ' '.join(sent_tokens)

def format_pred(pred, colors):
    ret = []
    args = pred.arguments
    corpula = '<span style=\\"background-color:%s\\">is/are</span>'%(colors['special'])

    if pred.type in {'poss'}:
        poss = '<span style=\\"background-color:%s\\">has/have</span>'%(colors['special'])
        return ' '.join([pred.arguments[0].name, poss, pred.arguments[1].name])

    if pred.type in {'amod', 'appos'}:
        # Special handling for `amod` and `appos` because the target
        # relation `is/are` deviates from the original word order.
        arg0 = None
        other_args = []
        for arg in pred.arguments:
            if arg.root == pred.root.gov:
                arg0 = arg
            else:
                other_args.append(arg)
        if arg0 is not None:
            ret = [arg0.name, corpula]
            args = other_args
        else:
            ret = [args[0].name, corpula]
            args = args[1:]

    # Mix arguments with predicate tokens. Use word order to derive a
    # nice-looking name.
    last_pred_token_pos, last_pred_token_index = -1, -1
    for idx, y in enumerate(sorted(pred.tokens + args)):
        if isinstance(y, Argument):
            ret.append(y.name)
            if (pred.root.gov_rel == 'xcomp' and
                pred.root.tag not in {'VERB', 'ADJ', 'JJ'} and
                idx == 0):
                ret.append(corpula)
        else:
            text = html_escape(y.text)
            if last_pred_token_pos == -1:
                text = '<span style=\\"background-color:%s\\">%s'%(colors['pred'], text)
                ret.append(text)
            else:
                if y.position-last_pred_token_pos != 1:
                    ret[last_pred_token_index] += '</span>'
                    text = '<span style=\\"background-color:%s\\">%s'%(colors['pred'], text)
                    ret.append(text)
                else:
                    ret.append(text)
            last_pred_token_pos = y.position
            last_pred_token_index = len(ret)-1
    ret[last_pred_token_index] += '</span>'
    return ' '.join(ret)

def arg_format(pred, arg, arg_i, colors):
    something = '<span style=\\"background-color:%s\\">SOMETHING</span>'%(colors['special'])
    arg_phrase = html_escape(' '.join(tk.text for tk in arg.tokens))
    arg_phrase = '<span style=\\"background-color:%s\\">%s</span>'%(colors['arg'][arg_i], arg_phrase)
    if (arg.root.gov_rel in {'ccomp', 'csubj', 'xcomp'}
        and arg.root.gov in pred.tokens and pred.type == 'normal'):
        s = something + ' := ' + arg_phrase
    else:
        s = arg_phrase
    return s

def extract():
    arg_color_list = ['#eeda6e', '#ff751a', '#00cc99', '00b33c', '#99b3ff', '#ff3333']
    colors = {'pred': '#dab3ff', 'arg': arg_color_list, 'special':'#ffffff'}
    sys_args = parse_args()
    f = open(sys_args.output, 'wb')
    writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
    writer.writerow(['json_variables'])
    row_i, row= 0, []
    for slabel, parse, ppatt in extract_predpattern(sys_args):
        if row_i > 10:
            break
        tokens = [html_escape(tk.text) for tk in ppatt.tokens]
        for pred in ppatt.instances:
            entails = {}
            hl_sent = highlight_sentence(tokens[:], pred, colors)
            if hl_sent == None:
                continue
            entails['questionID'] = 'q_%d'%(len(row)+1)
            entails['sentenceID'] = slabel
            entails['sentences'] = hl_sent
            entails['pred_id'] = '%s_%d'%(pred.type, pred.root.position)
            entails['predicate'] = '<div class=\\"statement_for_predicate\\">'
            entails['predicate'] += """<span style=\\"font-weight:normal;\\">Predicate:&nbsp;&nbsp;</span> """
            entails['predicate'] += format_pred(pred, colors) + '</div>'
            for arg_i, arg in enumerate(sorted(pred.arguments)):
                arg_i = arg_i%len(colors['arg'])
                entails['predicate'] += '<div class=\\"statement_for_argument\\">'
                entails['predicate'] += '<span style=\\"font-weight:normal;\\">%s:&nbsp;&nbsp;</span> '%(arg.name)
                entails['predicate'] += arg_format(pred, arg, arg_i, colors) + '</div>'
            row.append(entails)
            if len(row) == 5:
                writer.writerow([json.dumps(row, sort_keys=True)])
                row_i += 1
                row = []
    f.close()


if __name__ == "__main__":
  extract()


