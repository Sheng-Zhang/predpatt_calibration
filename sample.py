#!/usr/bin/env python
# encoding: utf-8

import sys, os, timeit
import random
import codecs
from concrete.util.file_io import CommunicationReader
from predpatt import CommUtil

def reservoir_sample(l, k):
    ret = []
    for i, item in enumerate(l):
        if i%1000 == 0:
            print '+',
            sys.stdout.flush()
        if i < k:
            ret.append(item)
        else:
            j = random.randint(1, i+1)
            if j <= k:
                ret[j-1] = item
    print '\n#######%d'%(i+1)
    return ret

def gen_comm(filepath):
    tool='ud converted ptb trees using PyStanfordDependencies_v0.3.1'
    for comm, filename in CommunicationReader(filepath):
        for sent_i , (slabel, parse) in enumerate(CommUtil.load_comm(comm, tool), 1):
            idx = '# %s__%d'%(filename, sent_i)
            yield idx, parse

def dump(r, output):
    utils_path = '/home/zhangsheng/projects/local_utils'
    from universal_tags import convert
    f = open(output, 'w')
    ret = []
    for idx, parse in r:
        lines = [idx]
        for i, tk in enumerate(parse.tokens):
            gov = parse.governor[i]
            conll_str = '\t'.join(
                        map(str,[i+1,
                                 tk.encode('utf-8'),
                                 parse.lemmas[i].encode('utf-8'),
                                 convert('en-ptb',
                                         parse.tags[i],
                                         utils_path+'/universal-pos-tags'),
                                 parse.tags[i],
                                 '_',
                                 gov.gov+1,
                                 gov.rel,
                                 '_',
                                 '_']))
            lines.append(conll_str)
        ret.append('\n'.join(lines))
    print >> f, '\n\n'.join(ret)
    f.close()

def sample(k, filepath, output):
    l = gen_comm(filepath)
    r = reservoir_sample(l, k)
    # r = test(l, k)
    dump(r, output)

def multi_sample(k, fl, path, out, mod):
    for i, filename in enumerate(open(fl), 1):
        # if i%20 != mod:
        #     continue
        filename = filename.strip()
        filepath = os.path.join(path, filename)
        name = filename.split('.')[0]
        outpath = os.path.join(out, name)
        print "%s => start!"%(filename)
        sys.stdout.flush()
        start_time = timeit.default_timer()
        sample(k, filepath, outpath)
        end_time = timeit.default_timer()
        print "%s => Time elasped: %.2fm"%(filename, (end_time-start_time)/60.)
        print ''
        sys.stdout.flush()

def sub_sample(n, count_file, path):
    count = (l.strip().split('\t') for l in open(count_file))
    count = {k:int(v) for k, v in count}
    total, aggre_c  = sum(count.itervalues()), 0
    ret = []
    for f, sent_c in count.iteritems():
        filename = f.split('.')[0]
        # if i == len(count):
        #     sample_c = n - aggre_c
        # else:
        #     sample_c = int((sent_c/total+0.)*n)
        # print >> sys.stderr, filename, sample_c, sent_c
        # aggre_c += sample_c
        filepath = os.path.join(path, filename)
        temp = open(filepath).read().decode('utf-8').split('\n\n')
        if len(temp) != 1000:
            print >> sys.stderr, filename, len(temp)
        ret += temp
    random.shuffle(ret)
    print len(ret)
    # print '\n\n'.join(ret[:n])


def test(l, k):
    ret = []
    for i, item in enumerate(l):
        if i > k:
            break
        ret.append(item)
    return ret

if __name__ == '__main__':
    sys.stdout  = codecs.getwriter('utf8')(sys.stdout)
    # n, count_file, path = sys.argv[1:]
    # sub_sample(int(n), count_file, path)

    # k, filepath, output = sys.argv[1:]
    # sample(int(k), filepath, output)

    k, filelist, path, out, mod = sys.argv[1:]
    start_time = timeit.default_timer()
    multi_sample(int(k), filelist, path, out, int(mod))
    end_time = timeit.default_timer()
    print "\nTotal Time elasped: %.2fm"%((end_time-start_time)/60.)

