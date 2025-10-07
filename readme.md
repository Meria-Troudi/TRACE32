--------------------------------------------------------------------------------
@Title: Automate TRACE32 Flash Programming with Python & CANoe
@Description: This solution enables automated execution and validation of TRACE32 CMM scripts 
using Python as a backend server, integrated with CANoe test frameworks.
@Keywords: TRACE32, Python, CANoe, CMM, automation, script, validation, TCP ,API
@Author: 
@Version: 1.0
@Date: 2025-08-06

--------------------------------------------------------------------------------

PROJECT STRUCTURE

project-root/
│
├── CLI.py                  # Python TCP server entry point; accepts commands like RUN_CMM|path|count
├── run_cmm.py              # Manages TRACE32 instance and communicates via DLL
├── launcher.py             # CAPL test function to validate input, run test, and parse result
├── auto-config.py         # CAPL script to auto-detect and validate environment
├── caplnode.can            # CANoe CAPL script to start Python server, manage state, and send/receive TCP messages
├── tf.can                  # CAPL test function to validate input, run test, and parse result
├── config.ini              # Configuration file with absolute paths for TRACE32 and CLI


## Requirements

### Hardware
- Windows PC (64-bit)  
- USB/JTAG Debugger (e.g., Lauterbach)  
- Sufficient RAM and CPU resources for parallel execution

### Software
- Python 3.7 or later (3.11+ recommended)  
- TRACE32 with correct executable and DLL  
- CANoe with CAPL scripting support  
- Windows OS with Administrator privileges (required for process management and TCP port binding)

### Dependencies
- Python standard library only: `socket`, `threading`, `subprocess`, `ctypes`, `configparser`  
- No external Python packages required

### INSTALLATION & SETUP

### Step 1: Install Python
Download Python 3.11+ from https://www.python.org
During installation, add Python to your PATH
Verify installation:  python --version

### Step 2: Configure TRACE32 Paths
Run the following command to extract valid TRACE32 launch settings:
      Open TRACE32 manually
      Right-click → Environment File
      Copy the launch command, like:
               start C:\T32\t32marm.exe -c C:\Users\<user>\temp\.t32
      
Copy the executable and config paths into config.ini:
      [trace32]
      trace32_exe = C:\T32\t32marm.exe
      trace32_dll = C:\T32\api\python\t32api64.dll
      trace32_config = C:\Users\<user>\temp\.t32
You may also run launcher.py to auto-detect and create this config file.

### Step 3: Adjust CAPL Script
Edit caplnode.can or any related CAPL file to launch the Python server using sysExec:
on start {
  write("? Node start: launching Python server");

  sysExec("C:\\Path\\To\\Python311\\python.exe", "CLI.py", "C:\\Path\\To\\Project");
}
Use where python in CMD to find the correct Python path on your system.t 



### How It Works: End-to-End Workflow

### Step 1: Initialize Environment

   Run launcher.py once.
   It auto-detects essential paths or allows manual input.
   Saves configuration to config.ini.
   Automatically launches TRACE32 and CANoe with configured settings.

### Step 2: Start CANoe 

   The simulation starts with CANoe open.
   The CAPL script (caplnode.can) does the following:
      Starts the Python TCP server (CLI.py)
      Monitors relevant global/system variables 
      Sends commands to the Python server via TCP port 

### Step 3: Execute TRACE32 CMM from CANoe
The Python server:

Launches TRACE32 via run_cmm.py

Loads and executes the .cmm script the specified number of times

Returns execution result (OK, FAIL, or error message) back to CANoe via TCP

Ensure:
   t32marm.exe launches correctly with your .t32 config
   t32api64.dll matches your CPU architecture (x64 or x86)

### Step 4: Monitor Execution and Results
   Python server logs TRACE32 activity and errors to its console
   CANoe reads result to determine test pass/fail
   Any script or TRACE32 errors are visible in the Python console output


### Troubleshooting & Tips
TRACE32 crashes or doesn't load config?
   Double-check trace32_exe and trace32_config paths. Try launching manually with:
   start C:\T32\t32marm.exe -c C:\Users\you\.t32
Nothing happens in CANoe?
   Ensure CAPL sysExec() points to the correct Python and project directory. Look at CAPL log output.

Server not responding?
      Check that CLI.py is running.
      Confirm port 12345 is free.
      Use netstat -aon | find "12345" to debug.

Use consistent versions
      Python 3.7+
      TRACE32 DLL: Match CPU architecture
      Don’t mix 32-bit and 64-bit binaries

### Security Advisory
   Ensure CLI.py runs in a secure, controlled environment.
   Port 12345 should not be exposed beyond the local machine or trusted network.
   CAPL sysExec allows arbitrary command execution — do not use in untrusted test environments.
