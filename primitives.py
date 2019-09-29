#!/usr/bin/env python3

import os
import csv
import re

import pandas as pd


CHANNEL_RE = re.compile(r'/(?P<type>.*?)/(?P<ch_num>\d\d)/config '
                        r'"(?P<name>.*)" '
                        r'(?P<pic_num>\d+) (?P<color>.*)( (?P<input>\d+))?')


def is_logicx(file_name):
    return re.match(r'(?P<base>.*).logicx', file_name)


def is_scn(file_name):
    return re.match(r'(?P<base>.*).scn', file_name)


def _get_name_df(csv_file=None):
    manualflag = False
    while True:
        if csv_file is None:
            manualflag = True
            file_name = input('Specify a .csv file to load. Exit with "q".\n')
        else:
            file_name = csv_file
        if file_name == 'q':
            return
        if not os.path.exists(csv_file):
            print(f'Error: File {csv_file} does not exist.')
            if manualflag:
                continue
        break
    with open(file_name, 'r') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        sep = dialect.delimiter
    df = pd.read_csv(file_name, sep=sep)
    if 'Base' not in df.columns:
        print('No Base Session exists. It must be named Base.')
        return
    df = df.fillna('')
    df = df.set_index('Base')
    return df
