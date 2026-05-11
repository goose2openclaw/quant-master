#!/usr/bin/env python3
'''
G27 Oracle Trading System - APK Entry Point
'''

import sys
import os

# Add skills path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from g27_autonomous import main

if __name__ == '__main__':
    main()
