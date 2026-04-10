# registry.py
from trace32.run_cmm import run_cmm

from vflash.run_vflash import run_vflash

TOOL_REGISTRY = {
    "TRACE32": {
        "runner": run_cmm,
        "description": "Execute TRACE32 CMM script"
    },

    "VFLASH": {
        "runner": run_vflash,
        "description": "Execute vFlash project"
    }
}