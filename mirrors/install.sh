#!/bin/sh

# make our owned directories
mkdir -m 0755 -p /var/{run,lib,lock,log}/mirrormanager /etc/mirrormanager
chown mirrormanager:mirrormanager /var/{run,lib,lock,log}/mirrormanager /etc/mirrormanager
