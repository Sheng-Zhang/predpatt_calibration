#!/usr/bin/env python
# encoding: utf-8

import sys, csv, json
from statistics import fleiss_kappa
import itertools
sys.path.insert(0, '/home/zhangsheng/.local/lib/python2.7/site-packages')
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
    def __init__(self, pred_id, pred, question):
        self.pred_id = pred_id
        self.pred_html = pred
        self.workers = []
        self.question = question

class Sentence:
    """
    Define the sentence class.

    """

    def __init__(self, q):
        self.sentid = q['sentenceID']
        self.sentence_html = q['sentences']
        self.predicates = {}

    def add_worker(self, q, row):
        # get predicate
        pred_id = q['pred_id']
        pred_html = q['predicate']
        id_ = pred_id+pred_html
        if id_ in self.predicates:
            pred = self.predicates[id_]
        else:
            pred = Predicate(pred_id, q['predicate'], q)
            self.predicates[id_] = pred

        # get the worker number which is consistent with the question number
        i = q['questionID']

        # add worker to predicate
        workerid = row['WorkerId']
        answer = row['Answer.correctness_'+i]
        worker = Worker(workerid, answer)
        pred.workers.append(worker)

    def gen_answers(self):
        for pred in self.predicates.itervalues():
            answers = [worker.answer for worker in pred.workers]
            distr = [0, 0]
            for answer in answers:
                distr[answer] += 1
            yield pred, distr, answers

    def gen_answer_pairs(self):
        for pred in self.predicates.itervalues():
            answers = [worker.answer for worker in pred.workers]
            for s1, s2, in itertools.combinations(answers, 2):
                yield [s1], [s2]


def load_result(filepath):
    results = {}
    with open(filepath) as csv_file:
        reader = csv.DictReader(csv_file)
        for i, row in enumerate(reader):
            json_var = json.loads(row['Input.json_variables'])
            for q in json_var:
                sentid = q['sentenceID']
                # create sent object if it is not existed
                if sentid not in results:
                    sent = Sentence(q)
                    results[sentid] = sent
                else:
                    sent = results[sentid]
                # add worker
                sent.add_worker(q, row)
    print len(results)
    return results

def stratify_results(results):
    ret = {5:[], 4:[], 3:[], 2:[], 1:[], 0:[]}
    for sent in results.itervalues():
        for pred, distr, _ in sent.gen_answers():
            ret[distr[1]].append(pred.question)
    for k, v in ret.iteritems():
        print k, len(v)
    with open('stratified.csv', 'wb') as f:
        writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerow(['json_variables'])
        for agreement in sorted(ret.keys(), key=lambda x: -x):
            writer.writerow([json.dumps(ret[agreement], sort_keys=True)])



def cal_fleiss_kappa(results):
    mat = []
    for sent in results.itervalues():
        for _, distr, _ in sent.gen_answers():
            mat.append(distr)
    print len(mat)
    ret = fleiss_kappa(mat)
    print "The fleiss_kappa value of all HITs is %f."%(ret)

def cal_cohen_kappa(results):
    values = []
    for sent in results.itervalues():
        for s1, s2 in sent.gen_answer_pairs():
            kappa_value = skll.kappa(s1, s2,
                                     weights='quadratic')
            values.append(kappa_value)
    avg_kappa =  sum(values)/(len(values)+0.0)
    print "The average kappa value of all HITs is %f."%(avg_kappa)

def main(filepath):
    results = load_result(filepath)
    # from plot import boxplot
    # boxplot(results)
    stratify_results(results)
    cal_fleiss_kappa(results)
    cal_cohen_kappa(results)

if __name__ == '__main__':
    main(sys.argv[1])


