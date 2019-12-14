#!/usr/env/bin python3

import re
import sys
import shutil
import os
import fileinput
import csv

import pandas as pd

import primitives

MAX_BLOCKS = 4
BLOCK_SIZE = 8


def nz_mod(a, b):
    if not a % b:
        return b
    else:
        return a % b


def _change_scene_name(wip_file, new_name):
    for line in fileinput.input(wip_file, inplace=True):
        m = re.match(r'(?P<pre>#.*# )".*?"(?P<post> .*)$',
                     line)
        if m is not None:
            print(f'{m.group("pre")}"{new_name}"{m.group("post")}')
        else:
            print(line, end='')
    fileinput.close()


def swap_channels(wip_file, swap_dict):
    for line in fileinput.input(wip_file, inplace=True):
        for channel in swap_dict:
            m = re.match(fr'/ch/{channel:0>2}/(?P<Payload>.*)$',  # noqa E
                         line)
            if m is not None:
                print((f'/ch/{swap_dict[channel]:0>2}/'
                       f'{m.group("Payload")}'))
                break
        else:
            print(line, end='')
    fileinput.close()


def rename(wip_file, rename_dict, mode):
    failed = {**rename_dict}
    enabled = set()
    for c in mode:
        if c == 'a':
            enabled.add('auxin')
        elif c == 'b':
            enabled.add('bus')
        elif c == 'c':
            enabled.add('ch')
        else:
            print(f'Error: mode bit {c} does not exist.')
            return
    status = ''
    for line in fileinput.input(wip_file, inplace=True):
        m = primitives.CHANNEL_RE.match(line)
        if m is None:
            print(line, end='')
            continue
        else:
            status += "Matched: " + line
        # get data for the match
        ch_type = m.group('type')
        ch_num = m.group('ch_num')
        ch_name = m.group('name')
        ch_pic_num = m.group('pic_num')
        ch_color = m.group('color')
        # the channel type was not enabled. do not change the line
        if ch_type not in enabled:
            print(line, end='')
            continue
        for name in rename_dict:
            if ch_name != name:
                continue
            # get the input if an auxin or regular channel was matched
            if ch_type == 'auxin' or ch_type == 'ch':
                ch_input = m.group('input')
            else:
                ch_input = ''
            status += (f'\n{ch_type.upper()} '
                       f'{m.group("ch_num")}: '
                       f'{name} -> {rename_dict[name]}')
            if rename_dict[name] is '':
                status += 'turned OFF.'
                ch_pic_num = '1'
                ch_color = 'OFF'
                ch_input = '0'
            # this name has been found.
            if name in failed:
                failed.pop(name)
            print(f'/{ch_type}/{ch_num}/config '
                  f'"{rename_dict[name]}" {ch_pic_num} {ch_color} {ch_input}')
            break
        else:
            status += "Did not find the name in rename_dict. not changing"
            print(line, end='')
    fileinput.close()
    status += '\n'.join([f'Failed to find {k} to {v}'
                         for k, v in failed.items()])
    print(status)
    return status


def show_scene(wip_file):
    name_dict = {}
    with open(wip_file, 'r') as f:
        for line in f:
            m = re.match(r'/ch/(?P<ch_num>\d\d)/config "(?P<name>.*?)" .*$',
                         line)
            if m is not None:
                name_dict[int(m.group('ch_num'))] = m.group('name')
    # the longest channel name in the scene
    max_name_len = {i: max([len(v)
                            for k, v in name_dict.items()
                            if (nz_mod(k, BLOCK_SIZE) == i)] + [7])
                    for i in range(1, BLOCK_SIZE + 1)}
    print()
    for j in range(MAX_BLOCKS):
        # there are no channels anymore
        if len(name_dict) < j * BLOCK_SIZE:
            break
        # numbers of channels on this line
        chans_on_line = min(len(name_dict) - BLOCK_SIZE * j, BLOCK_SIZE)
        # length of this line in characters
        line_len = sum((v + 3 for k, v in max_name_len.items()
                        if nz_mod(k, BLOCK_SIZE) <= chans_on_line)) + 1
        tmp1 = ''
        tmp2 = ''
        for i in range(chans_on_line):
            col_len = max_name_len[i + 1] + 2
            tmp1 += f'|{"CH " + str(j * BLOCK_SIZE + i + 1):^{col_len}s}'  # noqa E501
            tmp2 += f'|{name_dict[j * BLOCK_SIZE + i + 1]:^{col_len}s}'  # noqa E501
        tmp1 += '|'
        tmp2 += '|'
        # print row header line
        print('-' * line_len)
        # print channel numbers
        print(tmp1)
        # print channel names
        print(tmp2)
    print()


def pair_swap(wip_file):
    swap_list = []
    print('Give all pairs seperated by spaces. '
          'Each pair on a new line. "c" to end.')
    while True:
        try:
            first_chan, second_chan = input().split()
        except ValueError:
            break
        try:
            first_chan = int(first_chan)
            second_chan = int(second_chan)
        except ValueError:
            break
        swap_list.append((first_chan, second_chan))
    flat_list = [el for tup in swap_list for el in tup]
    if len(flat_list) != len(set(flat_list)):
        print('Channel swapped more then once. Aborting.')
        sys.exit()
    # add swapback
    swap_dict = {k: v
                 for first, second in swap_list
                 for k, v in ((first, second), (second, first))}
    swap_channels(wip_file, swap_dict)
    print('Done.')


def swap_chain(wip_file):
    while True:
        to_swap = input('Which Channel do you want to move?\n')
        new_pos = input('Where do you want to put the channel?\n')
        try:
            to_swap = int(to_swap)
            new_pos = int(new_pos)
        except ValueError:
            print('Please enter two integers.')
            continue
        if to_swap not in range(1, 33) or new_pos not in range(1, 33):
            print('Channel numbers go from 1 to 32.')
            continue
        break
    direction = (to_swap - new_pos) // abs(to_swap - new_pos)
    smaller = min(to_swap, new_pos)
    bigger = max(to_swap, new_pos)
    swap_dict = {k: k + direction
                 for k in range(smaller + (direction < 0),
                                bigger + (direction < 0))}
    swap_dict[to_swap] = new_pos
    swap_channels(wip_file, swap_dict)
    print('Done.')


def batch_rename(wip_file):
    rename_dict = {}
    while True:
        try:
            to_rename, new_name = input('Specify "oldname newname". '
                                        '"c" to quit.\n').split()
        except ValueError:
            break
        rename_dict[to_rename] = new_name
    return rename(wip_file, rename_dict, 'abc')


def name_from_csv(wip_file, csv_file=None):
    df = _get_name_df(csv_file=csv_file)
    if df is None:
        return
    while True:
        session_to_load = input(('Specify one of these existing Sessions to '
                                'load names from:\n') +
                                ', '.join(list(df.columns)) + '\n')
        if session_to_load not in df.columns:
            print('Please choose an existing Session.')
            continue
        break
    rename_dict = {}
    for row in df.iterrows():
        rename_dict[row[0]] = row[1][session_to_load]
    return rename(wip_file, rename_dict, 'abc')


def create_named_scenes(wip_file, target_dir=None,
                        csv_file=None):
    # the local backup for this function
    loc_backup = ''
    # get a target_dir to work to
    if target_dir is None:
        target_dir = input('Specify a target directory.\n')
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
    elif not os.path.isdir(target_dir):
        print(f'Error: {target_dir} is a file.')
    # get the dataframe for names
    df = primitives._get_name_df(csv_file)
    if df is None:
        return
    count = 0
    m = re.match(r'(\.)?(?P<pref>.*)\..*(\.wip)?$', wip_file)
    if m is None:
        print('Failure. Nothing written.')
        return
    prefix = m.group('pref')
    prefix = os.path.basename(prefix)
    for session_name in df.columns:
        if session_name.startswith('#'):
            continue
        rename_dict = {row[0]: row[1][session_name] for row in df.iterrows()}
        loc_backup = save_backup(wip_file, '', silent=True)
        try:
            rename(wip_file, rename_dict, 'abc')
            _change_scene_name(wip_file, f'{prefix}_{session_name}')
            shutil.copy(wip_file, os.path.join(target_dir,
                                               f'{prefix}_{session_name}.scn'))
        except Exception as e:
            raise e
        finally:
            revert_from_backup(wip_file, backup=loc_backup)
        count += 1
    purge(loc_backup)
    print(f'Scene create done for {wip_file}. '
          f'Created {count} new scenes in {target_dir}.')


def save_backup(wip_file, new_file_name=None, silent=False):
    if new_file_name is None:
        new_file_name = input('Specify a name for the backup '
                              'or leave blank for automatic name.\n')
    if new_file_name == '':
        new_file_name = wip_file + '.backup'
    if not os.path.exists(new_file_name):
        os.makedirs(os.path.dirname(new_file_name), exist_ok=True)
    shutil.copy(wip_file, new_file_name)
    if not silent:
        print(f'Saved backup as {new_file_name}')
    return new_file_name


def revert_from_backup(wip_file, backup=''):
    if backup == '':
        print('No backup was set.')
        return
    shutil.copy(backup, wip_file)


def purge(scene):
    if os.path.exists(scene):
        os.remove(scene)


def export_changes(wip_file):
    export_name = input('Enter the name for the file to export to.\n')
    if export_name in os.listdir():
        confirm = input('Error: file exists. Do you want to override? (y/n)\n')
        if confirm == 'y':
            os.remove(export_name)
        else:
            return
    shutil.copy(wip_file, export_name)
    print(f'Done. State saved to {export_name}.')


def main():
    if len(sys.argv) == 1:
        scene = input('Specify a file to work on:\n')
    else:
        scene = sys.argv[1]
    global wip_file
    global backup
    wip_file = os.path.join(os.path.dirname(scene),
                            '.' + os.path.basename(scene) + '.wip')
    wip_file = shutil.copy(scene, wip_file)
    backup = shutil.copy(wip_file, wip_file + '.backup')
    if not os.path.exists(scene):
        print('Error: specified scene file does not exist.')
        return
    if len(sys.argv) <= 2:
        print('Welcome to the x32 toolkit.\n'
              'Swap pairs of channels with "pairs".\n'
              'Swap a specified channel to a new place with "chain".\n'
              'Show Channel Names for this scene with "names".\n'
              'Rename Channels with "rename".\n'
              'Load Names from csv with "load".\n'
              'Save backup with "backup".\n'
              'Revert the original file to the Backup with "revert".\n'
              'Export the current state to a new file with "export".\n'
              'Create all named Sessionfiles '
              'from this scene as base with "create".\n'
              'Quit this programm with "quit".')
    first_round_flag = True
    while True:
        if first_round_flag and len(sys.argv) > 2:
            command = sys.argv[2]
            first_round_flag = False
        else:
            command = input('X32Toolkit>>')
        if command.startswith('q') or command.startswith('Q'):
            break
        elif command == 'pairs' or command == 'p':
            print('Swapping pairs.')
            pair_swap(wip_file)
        elif command == 'chain' or command == 'c':
            print('Swapping chain.')
            swap_chain(wip_file)
        elif command == 'names' or command == 'n':
            show_scene(wip_file)
        elif command == 'rename' or command == 're':
            status = batch_rename(wip_file)
            print('Done renaming the following names:')
            print(status)
        elif command == 'load' or command == 'ldc':
            print('Loading Names from CSV.')
            status = name_from_csv(wip_file)
            print('Done renaming the following names:')
            print(status)
        elif command == 'revert' or command == 'rev':
            revert_from_backup(wip_file, backup=backup)
            print(f'Restored last backup.')
        elif command == 'backup' or command == 'bak':
            backup = save_backup(wip_file)
        elif command == 'purge':
            purge(backup)
            print('Backup purged.')
        elif command == 'export' or command == 'ex':
            export_changes(wip_file)
        elif command == 'create' or command == 'cr':
            create_named_scenes(wip_file, backup=backup)
        else:
            print('Unsupported Operation.')


if __name__ == '__main__':
    try:
        main()
    except:  # noqa E722
        raise
    finally:
        purge(wip_file)
        purge(backup)
