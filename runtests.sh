#!/bin/bash

set -e

protoc --python_out=mirrorlist mirrormanager.proto
protoc --python_out=mirrormanager2/lib mirrormanager.proto

# Run Python 2 if it's available
if [ -x /usr/bin/py.test-2.7 ]; then
	PYTHONPATH=mirrormanager2 py.test-2.7 --cov=mirrormanager2 $*
fi

# Run Python 3 if it's available
if [ -x /usr/bin/py.test-3 ]; then
	# Ensure env uses Python 3
	mkdir -p .test-bin
	ln -sf /usr/bin/python3 .test-bin/python
	PATH="$PWD/.test-bin:$PATH" PYTHONPATH=mirrormanager2 py.test-3 --cov=mirrormanager2 $*
fi
