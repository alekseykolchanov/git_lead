#!/usr/bin/env python3

from subprocess import check_output
from subprocess import call
from datetime import datetime
from datetime import timedelta
import re

def parseLog(log):
    commit_logs = log.split('"0_0')[1:]
    logs = []
    for commit_log in commit_logs:
        logs.append(parseCommitLog(commit_log))
    return logs

def parseCommitLog(log):
    lines = log.split("\n")
    name_commit = parseCommitLogFirstLine(lines[0])
    file_changes = parseFileChanges(lines[1:])
    return StatCommitLog(name_commit[0], name_commit[1], file_changes)

def parseCommitLogFirstLine(name_commit_line):
    name_commit = name_commit_line[:-1].split(";;;")
    if len(name_commit) != 2:
        raise ValueError(name_commit_line)
    return name_commit[0], name_commit[1]

def parseFileChanges(file_changes_list):
    def parseFileName(file_name_part):
        file_names = file_name_part.split("=>")
        file_name = file_names[-1].strip()
        if len(file_name) < 1:
            raise ValueError(file_name_part)
        return file_name

    file_changes = []
    for file_change in file_changes_list:
        if len(file_change.strip()) == 0:
            continue

        parts = file_change.split("\t")
        if len(parts) != 3:
            print("file_change: ", file_change)
            raise ValueError(file_change)
        file_name = parseFileName(parts[2])
        file_changes.append(FileChange(file_name, int(parts[0]), int(parts[1])))
    return file_changes


class StatCommitLog:
    def __init__(self, user_name, commit_hash, file_changes):
        self.user_name = user_name
        self.commit_hash = commit_hash
        self.file_changes = file_changes

    def __repr__(self):
        return "StatCommitLog: user_name: {0}; commit_hash: {1}; file_changes: {2}".format(self.user_name,
         self.commit_hash, self.file_changes)
    
    def __eq__(self, other):
        return (self.user_name == other.user_name and self.commit_hash == self.commit_hash and self.file_changes == other.file_changes)

class FileChange:
    def __init__(self, file_name, inserts, deletions):
        self.file_name = file_name
        self.inserts = inserts
        self.deletions = deletions

    def __repr__(self):
        return "FileChange: {0}, {1}, {2}".format(self.file_name, self.inserts, self.deletions)

    def __eq__(self, other):
        return (self.file_name == other.file_name and self.inserts == other.inserts and self.deletions == other.deletions)




# Figure out which branch we're on
fetch_result = call(['git', 'fetch'])
if fetch_result != 0:
    print("Error on 'git fetch':", fetch_result)
    exit()

remote_branches_string = check_output(['git', 'branch', '-r']).decode().strip()
remote_branches = remote_branches_string.split("\n")
remote_branches = filter(lambda x: " -> " not in x, remote_branches)

# dates
time_delta = timedelta(seconds = 3600 * 24)
current_date = datetime.today()
after_date = (current_date - time_delta).isoformat()
before_date = current_date.isoformat()

# files to ignore
files_to_ignore = {"\\.storyboard$",
"\\.xib$",
"\\.xcodeproj/"}
files_to_ignore_regex = list(map(lambda x: re.compile(x), files_to_ignore))

# main code
commit_logs = []
for branch in remote_branches:
    clean_branch = branch.strip()
    log = check_output(['git', 'log', '--no-merges', '--numstat',
     '--ignore-all-space', '--ignore-blank-lines', '--after=' + after_date, '--before=' + before_date,
     '--pretty=format:"0_0%aN;;;%H"', clean_branch]).decode()
    commit_logs += parseLog(log)
users_commits = {}

for commit_log in commit_logs:
    if commit_log.user_name in users_commits:
        if commit_log.commit_hash in users_commits[commit_log.user_name]:
            if commit_log != users_commits[commit_log.user_name][commit_log.commit_hash]:
                raise ValueError()
            continue
        users_commits[commit_log.user_name][commit_log.commit_hash] = commit_log
        continue
    users_commits[commit_log.user_name] = { commit_log.commit_hash : commit_log }

managed_commits = set()
for user in users_commits:
    print(user)
    number_of_commits = 0
    number_of_insertions = 0
    number_of_deletions = 0
    for commit in users_commits[user]:
        commit_log = users_commits[user][commit]
        if commit in managed_commits:
            continue
        number_of_commits += 1
        managed_commits.add(commit_log.commit_hash)
        for file_change in commit_log.file_changes:
            file_name = file_change.file_name
            ignore_file = False
            
            for regex in files_to_ignore_regex:
                if regex.search(file_name) != None:
                    ignore_file = True
                    break
            if ignore_file == True:
                continue
            number_of_insertions += file_change.inserts
            number_of_deletions += file_change.deletions
    
    print("Commits: ", number_of_commits, "; +", number_of_insertions, " -", number_of_deletions)
    print("\n")

                
        
        


