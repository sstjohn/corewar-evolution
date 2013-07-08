#!/bin/sh

ssh-agent bash -c 'ssh-add sshkey 2>&1; git clone git@github.com:sstjohn/corewar-evolution.git werk'
ssh-agent bash -c 'ssh-add sshkey 2>&1; cd werk; ./run_once.sh'
