# TRACE32-0.2 Automation Framework

**Automated TRACE32 Flash Programming with Python & CANoe Integration**

This solution enables automated execution and validation of TRACE32 CMM scripts using Python as a backend server, integrated with CANoe test frameworks.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)

## 🎯 Overview

The TRACE32-0.2 framework provides a robust automation solution for embedded systems testing and programming. It bridges the gap between TRACE32 debugging/programming tools and CANoe test environments through a Python-based TCP server.

### Key Features

- **Automated CMM Script Execution**: Run TRACE32 CMM scripts programmatically
- **Multi-Tool Support**: Extensible framework supporting TRACE32, vFlash, and other tools
- **CANoe Integration**: Seamless integration with CANoe test environments
- **Real-time Monitoring**: Live execution monitoring and error detection
- **Configuration Management**: Auto-detection and wizard-based configuration
- **TCP Communication**: Reliable client-server communication protocol

## 🏗️ Architecture

```
┌─────────────────┐    TCP/IP    ┌─────────────────┐
│   CANoe Test    │◄────────────►│   Python CLI    │
│   Environment   │              │   Server        │
└─────────────────┘              └─────────────────┘
                                           │
                                           │ DLL/Process
                                           ▼
                                   ┌─────────────────┐
                                   │   TRACE32       │
                                   │   Application   │
                                   └─────────────────┘
```

### Core Components

1. **CLI.py**: Main Python TCP server that handles client requests
2. **Tool Registry**: Extensible system for managing different programming tools
3. **Configuration System**: Auto-detection and manual configuration capabilities
4. **TRACE32 Integration**: Direct communication with TRACE32 via DLL
5. **vFlash Integration**: Support for vFlash programming operations

## 📁 Project Structure

```
TRACE32 -0.2/
├── CLI.py                    # Main TCP server entry point
├── auto_config.py           # Configuration management and wizard
├── config.ini               # Application configuration
├── launcher.py              # TRACE32 launcher utility
├── registry.py              # Tool registry system
├── trace32_launcher.py      # TRACE32 process management
├── tools/
│   ├── trace32/
│   │   └── run_cmm.py       # TRACE32 CMM script execution
│   └── vflash/
│       └── run_vflash.py    # vFlash programming operations
├── dll/
│   ├── config.t32           # TRACE32 configuration
│   ├── t32api64.dll         # TRACE32 API library
│   └── vflash.ini           # vFlash configuration
├── assets/
│   ├── icon.ico             # Application icon
│   └── icon.png             # Application icon
└── canoe/
    ├── cap.can              # CANoe CAPL scripts
    ├── Configuration1.cfg   # CANoe configuration
    └── *.cbf, *.tse         # Test environment files
```

## 📋 Requirements

### Hardware Requirements
- Windows PC (64-bit)
- USB/JTAG Debugger (e.g., Lauterbach)
- Sufficient RAM and CPU resources for parallel execution

### Software Requirements
- **Python 3.7+** (3.11+ recommended)
- **TRACE32** with correct executable and DLL
- **CANoe** with CAPL scripting support
- **Windows OS** with Administrator privileges

### Dependencies
- Python standard library only:
  - `socket` - TCP communication
  - `threading` - Concurrent client handling
  - `subprocess` - Process management
  - `ctypes` - DLL interfacing
  - `configparser` - Configuration management

## ⚙️ Installation & Setup

### Step 1: Install Python
1. Download Python 3.11+ from [python.org](https://www.python.org)
2. During installation, ensure "Add Python to PATH" is checked
3. Verify installation: `python --version`

### Step 2: Configure TRACE32 Paths
1. Run the configuration wizard:
   ```bash
   python auto_config.py
   ```
2. The wizard will auto-detect TRACE32 components or allow manual selection
3. Configuration is saved to `config.ini`

### Step 3: Manual Configuration (Alternative)
Edit `config.ini` with your specific paths:
```ini
[paths]
trace32_exe=C:\Program Files\TRACE32\t32marm.exe
trace32_dll=C:\Program Files\TRACE32\api\python\t32api64.dll
trace32_config=C:\Users\username\.t32
canoe_cfg=C:\Path\To\Canoe\Project\config.cfg
tmp_dir=C:\Temp
cli=C:\Path\To\Project\CLI.py
```

### Step 4: Test Installation
```bash
python CLI.py
```
The server should start and listen on the configured port (default: 12345).

## 🔧 Configuration

### Configuration File Structure
```ini
[paths]
trace32_exe=...           # TRACE32 executable path
trace32_dll=...           # TRACE32 API DLL path
trace32_config=...        # TRACE32 configuration file
canoe_cfg=...             # CANoe configuration file
tmp_dir=...               # Temporary file directory
cli=...                   # CLI server script path

[runtime]
cli_host=localhost        # TCP server host
cli_port=12345           # TCP server port
trace32_node=localhost   # TRACE32 node name
trace32_port=20000       # TRACE32 port
trace32_packlen=1024     # TRACE32 packet length
timeout=20               # Script timeout in seconds
inactivity_timeout=5     # Inactivity timeout in seconds
```

### Auto-Configuration Wizard
The `auto_config.py` module provides a GUI wizard that:
- Auto-detects TRACE32 components
- Validates file paths
- Allows manual override
- Saves configuration to `config.ini`

## 🚀 Usage

### Starting the CLI Server
```bash
python CLI.py
```
The server will start and listen for incoming TCP connections.

### Client Communication Protocol

#### Command Format
```
RUN|PATH|INDEX
```

#### Examples
```
RUN|C:\scripts\flash.cmm|1
RUN|C:\projects\firmware.hex|2
RUN|C:\vflash\project.vf|3
```

#### Response Format
```
[PASS|FAIL]: [Message]
```

### Python Client Example
```python
import socket

def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 12345))
        s.sendall(command.encode())
        response = s.recv(4096)
        return response.decode()

# Execute CMM script
result = send_command("RUN|C:\\scripts\\flash.cmm|1")
print(f"Result: {result}")
```

### CANoe Integration
The framework includes CAPL scripts for CANoe integration:

```capl
on start {
  write("? Starting Python server...");
  sysExec("python.exe", "CLI.py", "C:\\Path\\To\\Project");
}

on sysvar TestScript {
  if (this == 1) {
    string result = sendCommand("RUN|C:\\scripts\\test.cmm|1");
    write("Test result: %s", result);
  }
}
```

## 📚 API Reference

### CLI Server Commands

#### RUN Command
Execute a script or programming operation.

**Format**: `RUN|PATH|INDEX`

**Parameters**:
- `PATH`: Absolute path to script/file
- `INDEX`: Execution index (for tracking multiple runs)

**Supported File Types**:
- `.cmm` - TRACE32 CMM scripts
- `.hex` - Intel HEX files
- `.vf` - vFlash projects
- Auto-detection based on path content

#### PING Command
Test server connectivity.

**Format**: `PING`

**Response**: `PONG`

### Tool Registry System

The framework uses a plugin-based tool registry system:

```python
from registry import TOOL_REGISTRY

# Register a new tool
TOOL_REGISTRY["MY_TOOL"] = {
    "runner": my_tool_function,
    "description": "Description of the tool"
}

def my_tool_function(path):
    # Implementation
    return "PASS: Operation completed"
```

### TRACE32 Integration

#### Core Functions
- `init_trace32()`: Initialize TRACE32 connection
- `run_cmm_script()`: Execute CMM script
- `wait_for_script_completion()`: Monitor script execution
- `collect_messages_and_detect_error()`: Capture output and errors

#### Error Detection
The system automatically detects errors through:
- TRACE32 status codes
- Message content analysis
- Timeout detection
- Keyword matching (fail, error, abort)

### vFlash Integration

#### Core Functions
- `vFlash.__init__()`: Initialize vFlash automation
- `run_vflash()`: Execute vFlash programming operation

## 🔧 Advanced Configuration

### Custom Tool Integration
1. Create your tool runner function
2. Register it in `registry.py`
3. Implement auto-detection logic in `CLI.py`

### Network Configuration
Modify `config.ini` to change network settings:
```ini
[runtime]
cli_host=0.0.0.0          # Listen on all interfaces
cli_port=8080            # Custom port
```

### Logging and Debugging
Enable verbose logging by modifying the server startup:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔍 Troubleshooting

### Common Issues

#### TRACE32 Not Launching
**Symptoms**: Server fails to connect to TRACE32
**Solutions**:
1. Verify `trace32_exe` path in config.ini
2. Check that TRACE32 is properly installed
3. Ensure no other TRACE32 instances are running
4. Verify DLL architecture (32-bit vs 64-bit)

#### Permission Errors
**Symptoms**: Access denied errors
**Solutions**:
1. Run as Administrator
2. Check file permissions on TRACE32 installation
3. Verify antivirus is not blocking the application

#### Network Connection Issues
**Symptoms**: Client cannot connect to server
**Solutions**:
1. Check firewall settings
2. Verify port is not in use: `netstat -aon | find "12345"`
3. Test with `telnet localhost 12345`
4. Check network configuration in config.ini

#### Script Execution Failures
**Symptoms**: Scripts fail to run or timeout
**Solutions**:
1. Verify script syntax and path
2. Check TRACE32 configuration
3. Increase timeout values in config.ini
4. Review TRACE32 console output

### Debug Mode
Enable debug logging in `CLI.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

### Log Files
The system generates logs in:
- Console output for real-time monitoring
- TRACE32 message capture for script analysis
- Error logs for troubleshooting

## 🔒 Security Considerations

### Network Security
- **Local Binding**: Server binds to localhost by default
- **Port Security**: Use non-standard ports in production
- **Firewall Rules**: Configure appropriate firewall rules
- **Network Isolation**: Use isolated networks for sensitive operations

### Process Security
- **Input Validation**: All file paths are validated
- **Command Injection**: Prevented through strict command parsing
- **File Access**: Limited to configured directories
- **Process Isolation**: Each client handled in separate thread

### Best Practices
1. **Environment Isolation**: Use dedicated test environments
2. **Access Control**: Limit access to configuration files
3. **Audit Logging**: Monitor all operations
4. **Regular Updates**: Keep all components updated

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to all functions
- Include error handling

### Testing
```bash
# Run basic functionality tests
python -m pytest tests/

# Test TRACE32 integration
python tests/test_trace32.py

# Test vFlash integration
python tests/test_vflash.py
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the configuration examples
- Contact the development team

## 🔄 Version History

### v0.2 (Current)
- Added vFlash integration
- Enhanced error detection
- Improved configuration management
- Added auto-detection wizard

### v0.1 (Initial)
- Basic TRACE32 CMM execution
- TCP server implementation
- Simple configuration system

---

**Note**: This framework is designed for professional embedded systems development and testing environments. Always follow your organization's security and development guidelines when using this tool.