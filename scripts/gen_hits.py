#!/usr/bin/env python
# encoding: utf-8

import csv
import json
import argparse
from predpatt.Predpattern import Predpattern, Argument, PredpattOpts
from predpatt import CommUtil
from utils import html_escape, ptb2text

arg_color_list = ['#fb8072', '#ffffb3', '#8dd3c7',
                  '#80b1d3', '#fdb462', '#b3de69',
                  '#fccde5', '#d9d9d9']
COLORS = {'pred': '#dab3ff', 'arg': arg_color_list, 'special': '#ffffff'}
corpula = ('<span id=\\"rcorner\\" style=\\"background-color:%s\\">'
           'is/are</span>' %(COLORS['special']))
opts = PredpattOpts(simple=False,
                    cut=False,
                    resolve_relcl=True,
                    resolve_amod=True,
                    resolve_poss=True,
                    resolve_appos=True,
                    resolve_conj=True)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
                        help='path to the input file. Accepts Concrete communications and CoNLLU formats.')
    parser.add_argument('output',
                        help='output')
    args = parser.parse_args()
    return args


def extract_predpattern(sys_args):
    for slabel, parse in CommUtil.load_conllu(sys_args.filename):
        parse.tokens = ptb2text(' '.join(parse.tokens)).split(' ')
        ppatt = Predpattern(parse, opts=opts)
        if ppatt:
            yield slabel, parse, ppatt


def highlight_sentence(sent_tokens, pred):
    def highlight(tokens, color):
        """
        Add html code to highlight specific *tokens* with specific
        *color* in sent_tokens.
        """
        if len(tokens) == 0:
            return None
        last_index = -1
        for tk in tokens:
            index = tk.position
            text = sent_tokens[index]
            if last_index == -1:
                sent_tokens[index] = ('<span id=\\"rcorner\\" style=\\"'
                                      'background-color:%s\\">%s'
                                      %(color, text))
            else:
                span = index - last_index
                if span != 1:
                    sent_tokens[last_index] += '</span>'
                    sent_tokens[index] = ('<span id=\\"rcorner\\" style=\\"'
                                          'background-color:%s\\">%s'
                                          %(color, text))
            last_index = index
        sent_tokens[last_index] += '</span>'

    if pred.type != 'poss':
        highlight(pred.tokens, COLORS['pred'])
    for arg_i, arg in enumerate(sort_by_position(pred.arguments)):
        arg_i = arg_i % len(COLORS['arg'])
        highlight(arg.tokens, COLORS['arg'][arg_i])

    return ' '.join(sent_tokens)


def format_poss(pred, placeholder):
    poss = ('<span id=\\"rcorner\\" style=\\"background-color:%s\\">'
            'has/have</span>' %(COLORS['special']))
    if placeholder:
        ret = ' '.join([pred.arguments[0].name, poss,
                        pred.arguments[1].name])
    else:
        arg_0 = format_arg(pred, pred.arguments[0], 0)
        arg_1 = format_arg(pred, pred.arguments[1], 1)
        ret = ' '.join([arg_0, poss, arg_1])
    return ret


def preprocess_modpred(pred, placeholder):
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
        arg_0 = (arg0.name if placeholder
                 else format_arg(pred, arg0, 0))
        ret = [arg_0, corpula]
        args = other_args
    else:
        arg_0 = (args[0].name if placeholder
                 else format_arg(pred, args[0], 0))
        ret = [arg_0, corpula]
        args = args[1:]
    return ret


def sort_by_position(x):
    return list(sorted(x, key=lambda y: y.position))


def format_pred(pred, placeholder):
    ret = []
    args = pred.arguments

    if pred.type in {'poss'}:
        return format_poss(pred, placeholder)

    arg_i = 0  # Count for current argument.

    if pred.type in {'amod', 'appos'}:
        ret += preprocess_modpred(pred, placeholder)
        arg_i = 1

    # Mix arguments with predicate tokens. Use word order to derive a
    # nice-looking name.
    last_pred_token_pos, last_pred_token_index = -1, -1
    for idx, y in enumerate(sort_by_position(pred.tokens + args)):
        if isinstance(y, Argument):
            if placeholder:
                arg = y.name
            else:
                arg = format_arg(pred, y, arg_i)
                arg_i += 1
            ret.append(arg)
            # TODO: explain the following condition
            # if (pred.root.gov_rel == 'xcomp' and
            #     pred.root.tag not in {'VERB', 'ADJ', 'JJ'} and
            #     idx == 0):
            #     ret.append(corpula)
        else:
            text = html_escape(y.text)
            if last_pred_token_pos == -1:
                # add html code to the first token of the predicate
                text = ('<span id=\\"rcorner\\" style=\\"'
                        'background-color:%s\\">%s' %(COLORS['pred'], text))
                ret.append(text)
            else:
                if y.position - last_pred_token_pos != 1:
                    # if there's argument in between
                    # add html code to end the span
                    ret[last_pred_token_index] += '</span>'
                    # add html code to start a new span
                    text = ('<span id=\\"rcorner\\" style=\\"background'
                            '-color:%s\\">%s' %(COLORS['pred'], text))
                    ret.append(text)
                else:
                    ret.append(text)
            last_pred_token_pos = y.position
            last_pred_token_index = len(ret) - 1
    ret[last_pred_token_index] += '</span>'
    return ' '.join(ret)


def format_arg(pred, arg, arg_i):
    something = ('<span id=\\"rcorner\\" style=\\"background-color:%s\\">'
                 'SOMETHING</span>' %(COLORS['special']))
    arg_phrase = html_escape(' '.join(tk.text for tk in arg.tokens))
    arg_phrase = ('<span id=\\"rcorner\\" style=\\"background-color:%s\\">'
                  '%s</span>' %(COLORS['arg'][arg_i], arg_phrase))
    if ((arg.root.gov_rel in {'ccomp', 'csubj', 'xcomp'}) and
            arg.root.gov in pred.tokens and pred.type == 'normal'):
        s = something + ' := ' + arg_phrase
    else:
        s = arg_phrase
    return s


def create_a_hit_element(qid, slabel, sent, html_sent, pred):
    pprint = pred.format(C=lambda x, _: x, track_rule=True)
    for a, b in (('\t', '\\t'), ('\n', '\\n')):
        pprint = pprint.replace(a, b)
    e = {}
    e['questionID'] = 'q_%d' %qid
    e['sentenceID'] = slabel
    e['sentence'] = html_escape(sent)
    e['html_sentence'] = html_sent
    e['pred_id'] = pred.identifier()
    e['pprint'] = html_escape(pprint)
    e['predicate'] = '<div class=\\"statement_for_predicate\\">'
    e['predicate'] += format_pred(pred, False) + '</div>'
    return e


def extract():
    sys_args = parse_args()
    f = open(sys_args.output, 'wb')
    writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
    writer.writerow(['json_variables'])
    row= []
    for slabel, parse, ppatt in extract_predpattern(sys_args):
        tokens = [html_escape(tk.text) for tk in ppatt.token]
        sent = ' '.join([tk.text for tk in ppatt.token])
        for pred in ppatt.instances:
            # only output normal output for now
            if pred.type != 'normal':
                continue
            # highlight argument phrases and return the whole sentence str
            html_sent = highlight_sentence(tokens[:], pred)
            if html_sent is None:
                continue
            # create an element for a hit quesiton
            e = create_a_hit_element(len(row) + 1, slabel, sent, html_sent,
                                     pred)
            row.append(e)
            if len(row) == 5:
                writer.writerow([json.dumps(row, sort_keys=True)])
                row = []
    f.close()


if __name__ == "__main__":
    extract()
