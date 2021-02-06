#!/bin/bash

zypper -n install cranix-radius
sed -i 's/CRANIX_RADIUS_REGISTER_DEVICE=*/CRANIX_RADIUS_REGISTER_DEVICE="yes"/' /etc/sysconfig/cranix
sed -i 's/CRANIX_FORCE_REGISTER_DEVICE=*/CRANIX_FORCE_REGISTER_DEVICE="yes"/' /etc/sysconfig/cranix

