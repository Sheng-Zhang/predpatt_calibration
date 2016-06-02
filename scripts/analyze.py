#!/usr/bin/env python
# encoding: utf-8

import sys
import csv
import json
from statistics import fleiss_kappa
import itertools
import skll


class Worker:
    """
    Define the worker for PredPatt calibration.

    """
    def __init__(self, workerid, answer):
        self.workerid = workerid
        self.answer = int(answer)


class Predicate:
    """
    Define the predicate class.

    """
    def __init__(self, hit_id, pred_id, pred, question, pprint=None):
        self.hit_id = hit_id
        self.pred_id = pred_id
        self.pred_html = pred
        self.workers = {}
        self.question = question
        if pprint:
            pprint = pprint.replace('\\t', '\t')
            pprint = pprint.replace('\\n', '\n')
            self.pprint = pprint


class Sentence:
    """
    Define the sentence class.

    """

    def __init__(self, q):
        self.sentid = q['sentenceID']
        self.sentence_html = q.get('sentence')  # q['sentence'])
        self.predicates = {}

    def add_worker(self, hit_id, q, row):
        # get predicate
        pred_id = q['pred_id']
        pred_html = q['predicate']
        id_ = pred_id + pred_html
        if id_ not in self.predicates:
            pred = Predicate(hit_id, pred_id, pred_html, q, q.get('pprint', None))
            self.predicates[id_] = pred
        pred = self.predicates[id_]

        # get the worker number which is consistent with the question number
        i = q['questionID']

        # add worker to predicate
        workerid = row['WorkerId']
        answer = row['Answer.correctness_' + i]
        worker = Worker(workerid, answer)
        pred.workers[workerid] = worker

    def gen_answers(self):
        for pred in self.predicates.itervalues():
            answers = [worker.answer for worker in pred.workers.itervalues()]
            distr = [0, 0]
            for answer in answers:
                distr[answer] += 1
            yield pred, distr, answers

    def gen_answer_pairs(self):
        for pred in self.predicates.itervalues():
            answers = [worker.answer for worker in pred.workers.itervalues()]
            for s1, s2, in itertools.combinations(answers, 2):
                yield s1, s2


def load_result(filepath):
    results = {}
    with open(filepath) as csv_file:
        reader = csv.DictReader(csv_file)
        for i, row in enumerate(reader):
            json_var = json.loads(row['Input.json_variables'])
            hit_id = row['Input.json_variables']
            for q in json_var:
                if 'normal' not in q['pred_id']:
                    continue
                sentid = q['sentenceID']
                # create sent object if it is not existed
                if sentid not in results:
                    sent = Sentence(q)
                    results[sentid] = sent
                sent = results[sentid]
                # add worker
                sent.add_worker(hit_id, q, row)
    print len(results)
    return results


def cal_fleiss_kappa(results):
    mat = []
    for sent in results.itervalues():
        for _, distr, _ in sent.gen_answers():
            mat.append(distr)
    print len(mat)
    ret = fleiss_kappa(mat)
    print "The fleiss_kappa value of all HITs is %f." %(ret)


def cal_pairwise_agreement(results):
    values = []
    for sent in results.itervalues():
        for s1, s2 in sent.gen_answer_pairs():
            pair_agreement = 1 if s1 == s2 else 0
            values.append(pair_agreement)
    avg_kappa = sum(values) / (len(values) + 0.0)
    print "The average pair-wise agreement of all HITs is %f." %(avg_kappa)


def cal_cohen_kappa_by_hit(results):
    # collect predicate by hit_id
    preds_by_hit = {}
    for sent in results.itervalues():
        for pred in sent.predicates.itervalues():
            if pred.hit_id not in preds_by_hit:
                preds_by_hit[pred.hit_id] = []
            preds_by_hit[pred.hit_id].append(pred)

    kappas = []
    # calculate kappa
    for preds in preds_by_hit.itervalues():
        # get answer list for each worker
        worker_answers_by_hit = {worker_id: [] for worker_id
                                 in preds[0].workers.keys()}
        for pred in preds:
            for worker in pred.workers.itervalues():
                worker_answers_by_hit[worker.workerid].append(worker.answer)

        # calculate kappa for each answer list pair
        worker_answers = worker_answers_by_hit.values()
        pairs_combinations = itertools.combinations(worker_answers, 2)
        for l1, l2 in pairs_combinations:
            kappa_value = skll.kappa(l1, l2)  #, weights='quadratic')
            kappas.append(kappa_value)
    avg_kappa = sum(kappas) / (len(kappas) + 0.0)
    print len(preds_by_hit)
    print "The average Cohen's kappa of all HITs is %f." %(avg_kappa)


def main(filepath):
    results = load_result(filepath)
    cal_pairwise_agreement(results)
    cal_fleiss_kappa(results)
    cal_cohen_kappa_by_hit(results)

if __name__ == '__main__':
    main(sys.argv[1])
