#!/usr/bin/env python3
# test_client.py — Test client for CLI.py simulation
# Uses the existing run_cmm.py and run_vflash.py functions

import socket
import sys
import time

HOST = "127.0.0.1"
PORT = 12345
EOT_MARKER = "<<<EOT>>>"

def send_command(command):
    """Send command to CLI.py server and receive response"""
    print(f"CLIENT: Sending command: {command}")
    
    try:
        with socket.create_connection((HOST, PORT), timeout=5) as s:
            print("CLIENT: Connected to server")
            
            # Send command
            s.sendall((command + "\n").encode())
            print(f"CLIENT: Sent: {command}")
            
            # Receive response
            response = b""
            start_time = time.time()
            
            while True:
                # Check for timeout
                if time.time() - start_time > 30:  # 30 second timeout
                    print("CLIENT: Timeout waiting for response")
                    break
                
                # Try to receive data
                try:
                    data = s.recv(1024)
                    if not data:
                        break
                    response += data
                    
                    # Check if we received the EOT marker
                    if EOT_MARKER.encode() in response:
                        break
                        
                except socket.timeout:
                    continue
            
            # Decode and display response
            response_text = response.decode(errors='ignore')
            print("CLIENT: Received response:")
            print("=" * 50)
            print(response_text)
            print("=" * 50)
            
            return response_text
            
    except ConnectionRefusedError:
        print("CLIENT: ERROR - Could not connect to server. Make sure CLI.py is running.")
        return None
    except Exception as e:
        print(f"CLIENT: ERROR - {e}")
        return None

def test_ping():
    """Test PING command"""
    print("\n" + "="*60)
    print("TEST 1: PING Command")
    print("="*60)
    response = send_command("PING")
    if response and "PONG" in response:
        print("✓ PING test passed")
    else:
        print("✗ PING test failed")

def test_run_cmm():
    """Test RUN_CMM command"""
    print("\n" + "="*60)
    print("TEST 2: RUN_CMM Command")
    print("="*60)
    
    # Test with example.cmm file
    test_file = "example.cmm"
    count = 2
    
    command = f"RUN_CMM|{test_file}|{count}"
    response = send_command(command)
    
    if response:
        if "SUCCESS" in response or "PASS" in response:
            print("✓ RUN_CMM test passed")
        elif "ERROR" in response:
            print("✗ RUN_CMM test failed with error")
        else:
            print("? RUN_CMM test completed (check output above)")
    else:
        print("✗ RUN_CMM test failed - no response")

def test_run_vflash():
    """Test RUN_VFLASH command"""
    print("\n" + "="*60)
    print("TEST 3: RUN_VFLASH Command")
    print("="*60)
    
    # Test with a sample vFlash project
    test_file = "sample_project.vfp"
    count = 1
    
    command = f"RUN_VFLASH|{test_file}|{count}"
    response = send_command(command)
    
    if response:
        if "SUCCESS" in response or "PASS" in response:
            print("✓ RUN_VFLASH test passed")
        elif "ERROR" in response:
            print("✗ RUN_VFLASH test failed with error")
        else:
            print("? RUN_VFLASH test completed (check output above)")
    else:
        print("✗ RUN_VFLASH test failed - no response")

def test_invalid_commands():
    """Test invalid commands"""
    print("\n" + "="*60)
    print("TEST 4: Invalid Commands")
    print("="*60)
    
    # Test invalid command
    response = send_command("INVALID_COMMAND|test|1")
    if response and "ERROR" in response:
        print("✓ Invalid command test passed")
    else:
        print("✗ Invalid command test failed")
    
    # Test missing parameters
    response = send_command("RUN_CMM|")
    if response and "ERROR" in response:
        print("✓ Missing parameters test passed")
    else:
        print("✗ Missing parameters test failed")

def test_tool_discovery():
    """Test tool discovery through registry"""
    print("\n" + "="*60)
    print("TEST 5: Tool Discovery")
    print("="*60)
    
    # Test unknown tool
    response = send_command("UNKNOWN_TOOL|test|1")
    if response and "Unknown command" in response:
        print("✓ Tool discovery test passed")
    else:
        print("✗ Tool discovery test failed")

def run_all_tests():
    """Run all tests"""
    print("TRACE32 -0.2 CLI.py Test Client")
    print("="*60)
    print("This client tests the CLI.py server functionality")
    print("Make sure CLI.py is running before starting tests")
    print("="*60)
    
    # Wait for user to start CLI.py
    input("\nPress Enter when CLI.py server is running...")
    
    # Run tests
    test_ping()
    test_run_cmm()
    test_run_vflash()
    test_invalid_commands()
    test_tool_discovery()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("Check the output above for test results")
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If command line arguments provided, run specific test
        if sys.argv[1] == "ping":
            test_ping()
        elif sys.argv[1] == "cmm":
            test_run_cmm()
        elif sys.argv[1] == "vflash":
            test_run_vflash()
        elif sys.argv[1] == "all":
            run_all_tests()
        else:
            print("Usage: python test_client.py [ping|cmm|vflash|all]")
    else:
        # Run interactive test suite
        run_all_tests()