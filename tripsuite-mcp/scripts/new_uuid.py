#!/usr/bin/env python3
"""Print N valid UUIDv4 values (default 1). Usage: new_uuid.py [N]"""
import sys, uuid

n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
for _ in range(n):
    print(uuid.uuid4())
