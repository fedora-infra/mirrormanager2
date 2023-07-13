#!/bin/bash

set -e

PATH="$PWD/.test-bin:$PATH" PYTHONPATH=mirrormanager2 MM2_CONFIG=./tests/mirrormanager2.cfg py.test-3 --cov=mirrormanager2 $*
