# predpatt_calibration

## Prerequisites
Install a specific commit of PredPatt first.
```bash
git clone https://gitlab.hltcoe.jhu.edu/extraction/PredPatt.git
git checkout ef31ebd3cf7f50fd7fdb73eb9b4fb4771d09af99
pip install .
```

## HIT Data Generation (csv files)
You can generate csv files from UD parses in CoNLL format. For example,
```bash
git clone https://github.com/sheng-z/predpatt_calibration.git
cd predpatt_calibration
python scripts/gen_hits.py samples/en_sample.conllu hits.csv
```

Example CoNLL files are in `samples`.

Example csv files are in `data/multi_lang_hits`.
