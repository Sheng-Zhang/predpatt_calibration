#!/usr/bin/env python
# encoding: utf-8

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def boxplot(results):
    plt.rcParams['figure.figsize'] = [64, 6]
    ret = []
    for hit in results.itervalues():
        for _, _, scores in hit.gen_answers():
            scores = np.array(scores)
            ret.append((np.mean(scores), scores))
    x = [v[1] for v in sorted(ret, key=lambda x: -x[0])]
    plt.boxplot(x, whis='range', showmeans=True,
                meanprops=dict(marker='s', markeredgecolor='green', markerfacecolor='green'),
                whiskerprops={'linewidth':2.5},
                medianprops={'linewidth':2.5},
                boxprops={'linewidth':2.5})
    plt.savefig('boxplot.png')
