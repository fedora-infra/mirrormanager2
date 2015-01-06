#!/bin/bash
#MM2_CONFIG=../tests/mm2_test.cfg PYTHONPATH=mirrormanager2 nosetests \

PYTHONPATH=mirrormanager2 nosetests \
--with-coverage --cover-erase --cover-package=mirrormanager2 $*
