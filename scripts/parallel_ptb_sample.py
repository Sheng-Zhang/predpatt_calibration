#!/usr/bin/env python
# encoding: utf-8

import sys
import os
from concrete.util.file_io import CommunicationReader
from concrete_util.io import gen_sent_from_comm
from concrete_util.export import export_ptb


def get_entries(filepath):
    """
    Get entry -- (comm_id, sent_i)  -- for each sample.

    """
    blocks = open(filepath).read().rstrip().split('\n\n')
    entries = []
    for block in blocks:
        comment_line = block.split('\n')[0]
        comm_id, sent_i = comment_line[2:].rsplit('__', 1)
        comm_id = comm_id.rsplit('.', 1)[0]
        sent_i = int(sent_i)
        sort_id = '%s.%04d' %(comm_id, sent_i)
        entries.append((sort_id, comm_id, sent_i))
    entries = sorted(entries, key=lambda x: x[0])
    return entries


def get_ptb_samples(gzfilepath, entries):
    """
    Get ptb samples from gzfile given their entries.

    """
    ret = []
    entry_length = len(entries)
    _, comm_id, sent_i = entries.pop(0)
    last_date = None
    sent_i = int(sent_i)
    print 'looking for %s at %d' %(comm_id, sent_i)
    for comm, filename in CommunicationReader(gzfilepath):
        current_date = comm.id.rsplit('.')[0]
        if current_date != last_date:
            last_date = current_date
            print current_date
            sys.stdout.flush()
        if comm.id != comm_id:
            continue
        for sent_j, sent in enumerate(gen_sent_from_comm(comm), 1):
            if sent_i == sent_j:
                print '+',
                sys.stdout.flush()
                for ptb_parse in sent.tokenization.parseList:
                    if ptb_parse.metadata.tool == 'Stanford CoreNLP':
                        ptb = export_ptb(ptb_parse.constituentList)
                        break
                ret.append((comm_id, sent_i, ptb.encode('utf-8')))
                if len(entries) == 0:
                    return ret
                _, comm_id, sent_i = entries.pop(0)
                sent_i = int(sent_i)
                print 'looking for %s at %d' %(comm_id, sent_i)
                if comm.id != comm_id:
                    break
    print >> sys.stderr, 'Missed ptb samples %d-%d: %s' %(entry_length,
                                                          len(ret),
                                                          gzfilepath)
    return ret


def output_ptb_samples(ptb_samples, output_filepath):
    """
    Output ptb sampels to output_filepath.

    """
    f = open(output_filepath, 'w')
    print >> f, '\n\n'.join('# %s__%d\n%s' %(comm_id, sent_i, ptb)
                            for comm_id, sent_i, ptb in ptb_samples)
    f.close()


def generate_parallel_ptb(samples_dirpath, gz_dirpath, output_dirpath):
    """
    Generate parrallel penn-treebank parses given ud samples.

    """
    for filename in os.listdir(samples_dirpath):
        print >> sys.stdout, filename
        sys.stdout.flush()
        filepath = os.path.join(samples_dirpath, filename)
        gzfilepath = os.path.join(gz_dirpath, filename + '.tar.gz')
        output_filepath = os.path.join(output_dirpath, filename)
        if os.path.isfile(output_filepath):
            continue

        # get entries
        entries = get_entries(filepath)

        # get ptb samples
        ptb_samples = get_ptb_samples(gzfilepath, entries)

        # output ptb samples
        output_ptb_samples(ptb_samples, output_filepath)
        print


def get_entries_from_hits_file(hits_filepath):
    """
    Get entries -- (sort_id, comm_id, sent_i) -- from hits file.
    Group them by their file_entry.
    Print the grouped entries.

    """
    import csv
    import json
    entries = {}
    sent_id_set = set()
    with open(hits_filepath) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            questions = json.loads(row['Input.json_variables'])
            for q in questions:
                sent_id = q['sentenceID']
                if sent_id in sent_id_set:
                    continue
                sent_id_set.add(sent_id)

                file_entry = sent_id[:14].lower()
                comm_id, sent_i = sent_id.rsplit('__', 1)
                sent_i = int(sent_i)
                comm_id = comm_id.rsplit('.', 1)[0]  # drop .comm suffix
                sort_id = '%s.%04d' %(comm_id, sent_i)
                if file_entry not in entries:
                    entries[file_entry] = []
                entries[file_entry].append((sort_id, comm_id, sent_i))
    for file_entry in entries:
        print '%s\t\t%s' %(file_entry, '\t\t'.join('%s\t%s\t%d' %i
                           for i in sorted(entries[file_entry],
                                           key=lambda x: x[0])))


def load_entries(lines):
    """
    Load entries from lines of entries.
    """
    def split_line(line):
        items = line.split('\t\t')
        return items[0], [i.split('\t') for i in items[1:]]
    return dict(split_line(line) for line in lines)


def main(entries_filepath, gz_dirpath, output_filepath, batch_i):
    # load_entries for batch_i
    batch_i = int(batch_i)
    lines = open(entries_filepath).read().split('\n')
    batch_size = len(lines) / 9
    lines = lines[(batch_i - 1) * batch_size: batch_i * batch_size]
    entries = load_entries(lines)
    print "%d entries loading from %d lines complete." %(len(entries), len(lines))

    # search parses
    ptb_parses = []
    for file_entry in entries:
        print "searching %d sentences in %s" %(len(entries[file_entry]), file_entry)
        gzfilepath = os.path.join(gz_dirpath, file_entry + '.tar.gz')
        ptb_parses += get_ptb_samples(gzfilepath, entries[file_entry])
        print

    output_ptb_samples(ptb_parses, output_filepath)


if __name__ == '__main__':
    # generate_parallel_ptb(*sys.argv[1:])
    main(*sys.argv[1:])
