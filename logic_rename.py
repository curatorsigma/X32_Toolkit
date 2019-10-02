#!/usr/bin/env python3

import re
import os
import sys
import fileinput
import shutil

import pandas as pd

import primitives

MAX_NAME_LEN = 20


def replace_ascii(string, old, new):
    if len(old) < len(new):
        old += '_' + (len(new) - len(old))
    elif len(old) > len(new):
        new += '_' + (len(old) - len(new))
    old_hex_encode = ''.join((f'{ord(c):02x}' for c in old))
    new_hex_encode = ''.join((f'{ord(c):02x}' for c in new))
    return re.sub(old_hex_encode, new_hex_encode, string)


def rename_in_file(file, rename_dict):
    """Rename all occurences of rename_dict.keys() with .values()

    Acts on the file ``file`` in-place. Writes in binary mode.

    Trailing ``_`` are replaced with spaces for each replacement.

    INPUTS
        string file: existing file.
        dict(string old: string new): what to replace."""
    # the block size to read at once
    SEARCH_BLOCK_SIZE = 1024 * 16
    with open(file, 'r+b') as f:
        while True:
            block = f.read(SEARCH_BLOCK_SIZE)
            if block == b'':
                break
            actual_read = len(block)
            for name, new_name in rename_dict.items():
                # search for the name until it can't be found anymore
                # we start to search at the block's start
                offset = 0
                # the last length of batch written to the file
                last_len = 0
                while True:
                    # only look after the last offset.
                    find_offset = block[offset + last_len:].find(name.encode())
                    # name can not be found
                    if find_offset == -1:
                        break
                    else:
                        # the actual offset from the fp is shifted by its
                        # last value (from last occurance of this name)
                        # it is additionally shifted by last_len, because we
                        # started the find last_len later to avoid circles
                        offset += find_offset + last_len
                        # save the current location
                        current_pos = f.tell()
                        # go to the location and replace
                        # we need to write one block earlier, but offset later
                        f.seek(offset - actual_read, 1)
                        # write the new name, then spaces to clean up
                        # rests of former names
                        overhang = max(len(name) - len(new_name), 0)
                        f.write(new_name.encode() +
                                b'\x20' * overhang)
                        # remove underscores from the end, replace w/ spaces:
                        char = b'\x5f'
                        i = 0
                        # if char is an underscore
                        while char == b'\x5f':
                            # write a space
                            f.write(b'\x20')
                            # increment the counter for last_len
                            i += 1
                            # read one char
                            char = f.read(1)
                            # and seek back to the same char we just read
                            f.seek(-1, 1)
                        last_len = len(new_name.encode()) + overhang + i
                        # go back to end of block for next occurance of name
                        f.seek(current_pos)


def create_named_projects(file, target_dir=None, csv_file=None):
    if target_dir is None:
        target_dir = input('Specify a target directory.\n')
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
    elif not os.path.isdir(target_dir):
        print(f'Error: {target_dir} is a file.')
    df = primitives._get_name_df(csv_file=csv_file)
    if df is None:
        return
    count = 0
    m = re.match(r'(?P<base>.*)\.logicx', file)
    if m is None:
        print('File has no logic project name.')
    base_name = m.group('base')
    base_name = os.path.basename(base_name)
    for session_name in df.columns:
        if session_name.startswith('#'):
            continue
        rename_dict = {row[0]: row[1][session_name] for row in df.iterrows()}
        # all names must end on '__' for unambiguity in the project file
        rename_dict = {k + '__': v if v != '' else '____EMPTY____'
                       for k, v in rename_dict.items() if len(k) > 0}
        # force the new names to be shorter then MAX_NAME_LEN
        rename_dict = {k: v[:MAX_NAME_LEN] for k, v in rename_dict.items()}
        new_file_name = os.path.join(target_dir,
                                     f'{base_name}_{session_name}.logicx')
        try:
            new_file = shutil.copytree(
                file,
                new_file_name)
        except FileExistsError:
            print(
                (f'The file {new_file_name} already exists.'))
            continue
        rename_in_file(os.path.join(new_file, 'Alternatives/000/ProjectData'),
                       rename_dict)
        count += 1
    print(f'Logic rename done for {file}. '
          f'Created {count} new projects in {target_dir}.')


def main():
    file = sys.argv[1]
    print('Welcome to the Logic Pro X Toolkit.\n'
          'Quit with "q".\n'
          'Create named projects according to some .csv file with "create".')
    while True:
        command = input('LPXToolkit>>')
        if command == 'q':
            break
        elif command == 'create' or command == 'cr':
            create_named_projects(file)


if __name__ == '__main__':
    main()
