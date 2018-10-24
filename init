#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
from pathlib import Path
from secrets import token_urlsafe


root = Path(__file__).parent

envfilename = root / '.env'

if envfilename.exists():
    sys.exit(1)

with open(envfilename, 'wt', encoding='UTF-8') as envfile:
    token = token_urlsafe()
    print(f'SECRET_KEY="{token}"', file=envfile)
    print('DEBUG=True', file=envfile)
