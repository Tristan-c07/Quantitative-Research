# -*- coding: utf-8 -*-
from jqdata import log

def log_kv(*args):
    """
    log_kv("a", 1, "b", 2) -> a=1 | b=2
    """
    if len(args) % 2 != 0:
        log.info("log_kv: bad args")
        return
    parts = []
    for i in range(0, len(args), 2):
        parts.append(f"{args[i]}={args[i+1]}")
    log.info(" | ".join(parts))
