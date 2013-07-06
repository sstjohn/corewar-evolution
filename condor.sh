#!/bin/sh

ssh-agent bash -c 'ssh-add sshkey; git clone git@github.com:sstjohn/corewar-evolution.git werk'
ssh-agent bash -c 'ssh-add sshkey; cd werk; ./run_once.sh'
