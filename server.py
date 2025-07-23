# test_runcmm.py

import runpy
import os
import json

# 1. Load your runcmm.py as a module
mod = runpy.run_path(r"C:\Users\meria\Desktop\TRACE32_TEST\TRACE32\example.cmm")
run_cmm = mod["run_cmm"]

def test_run_cmm():
    # 2. Prepare a dummy CMM file
    dummy = os.path.abspath("example.cmm")
    if not os.path.exists(dummy):
        with open(dummy, "w") as f:
            f.write('PRINT "Hello TRACE32"\nENDDO\n')

    print("▶ Invoking run_cmm on:", dummy)
    result = run_cmm(dummy)

    # 3. Parse & display
    try:
        data = json.loads(result)
        print("✔ Parsed JSON result:")
        for k,v in data.items():
            print(f"  {k}: {v}")
    except Exception:
        print("⚠️  Non-JSON or error output:")
        print(result)

if __name__ == "__main__":
    test_run_cmm()
