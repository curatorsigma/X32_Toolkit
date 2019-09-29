#!/usr/bin/env python3

import sys
import os
import re

import x32_toolkit
import logic_rename
import primitives


def main():
    csv_file = sys.argv[1]
    base_dir = sys.argv[2]
    target_dir = sys.argv[3]
    if target_dir[-1] == '/':
        target_dir = target_dir[:-1]
    for file in os.listdir(base_dir):
        file = os.path.join(base_dir, file)
        if primitives.is_logicx(file):
            logic_rename.create_named_projects(file, target_dir, csv_file)
        elif primitives.is_scn(file):
            x32_toolkit.create_named_scenes(
                wip_file=file, target_dir=target_dir,
                csv_file=csv_file)
        else:
            print(f'Unknown file {file}. Skipped.')  # noqa


if __name__ == '__main__':
    main()
