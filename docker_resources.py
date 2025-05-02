#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script for collecting Docker resource information on remote servers.
"""

import os
import sys
import time
import datetime
import argparse
from concurrent.futures import ThreadPoolExecutor

from server_info import ServerInfo
from formatters import format_output

# Default settings
DEFAULT_SERVERS_FILE = "servers.txt"
DEFAULT_OUTPUT_FORMAT = "text"
DEFAULT_TIMEOUT = 5  # Server connection timeout in seconds
MAX_WORKERS = 10  # Maximum number of parallel connections

def read_servers_file(file_path):
    """Read file with server list."""
    servers = []
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        print("Create a file in the format: user@hostname or hostname (one per line)")
        sys.exit(1)
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                servers.append(line)
    
    return servers

def process_server(server_address, key_file=None):
    """Process one server."""
    print(f"Checking server: {server_address}...")
    server_info = ServerInfo(server_address, key_file=key_file)
    success = server_info.collect_all_info()
    
    if success:
        print(f"Information collection for {server_address} completed successfully.")
    else:
        print(f"Error while collecting information for {server_address}: {server_info.error_message}")
        
    return server_info

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Script for checking Docker resources on servers.')
    parser.add_argument('-f', '--file', help='File with server list', default=DEFAULT_SERVERS_FILE)
    parser.add_argument('-o', '--output', help='File to write results')
    parser.add_argument('-k', '--key', help='SSH private key file')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default=DEFAULT_OUTPUT_FORMAT,
                        help='Results output format')
    args = parser.parse_args()
    
    # Read server list
    servers = read_servers_file(args.file)
    print(f"Found {len(servers)} servers to check.")
    
    # Use ThreadPoolExecutor for parallel server processing
    server_infos = []
    
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(servers))) as executor:
        futures = {
            executor.submit(process_server, server, args.key): server
            for server in servers
        }
        
        for future in futures:
            try:
                server_info = future.result()
                server_infos.append(server_info)
            except Exception as e:
                print(f"Error processing server {futures[future]}: {str(e)}")
    
    # Format and output results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output or f"docker_resources_{timestamp}.{args.format}"
    
    format_output(server_infos, args.format, output_file)

if __name__ == "__main__":
    main()