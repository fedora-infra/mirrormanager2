#!/bin/sh
for f in *.txt; do
    grep ^d $f | awk '{print $5'} > $(basename $f .txt)-dirsonly.txt
done
