#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for formatting server information output.
"""

import json
import datetime
from prettytable import PrettyTable

def format_text_output(server_infos, output_file=None):
    """Formatting output in text format."""
    # Create a table for summary
    table = PrettyTable()
    table.field_names = ["Server", "Port", "Status", "CPU (curr.)", "Load Avg (5m)", "Cores", "Memory", "Root Disk", "Cont. (act)", "Cont. (total)"]
    
    # Get summary information about each server
    summaries = [info.get_summary() for info in server_infos]
    
    for summary in summaries:
        if summary['status'] == 'available':
            table.add_row([
                summary['hostname'],
                summary['port'],
                summary['status'],
                summary['cpu_usage'],
                summary['cpu_load_relative'],
                summary['cpu_cores'],
                f"{summary['memory_usage']} ({summary['memory_percent']})",
                f"{summary['disk_usage']} ({summary['disk_percent']})",
                summary['containers_running'],
                summary['containers_total']
            ])
        else:
            table.add_row([
                summary['hostname'],
                summary['port'],
                f"{summary['status']}: {summary['error']}",
                "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"
            ])
    
    # 1. GENERAL SUMMARY
    output = "\n" + "=" * 80 + "\n"
    output += "SERVER SUMMARY\n"
    output += "=" * 80 + "\n"
    output += str(table) + "\n"
    
    # 2. DETAILED SERVER INFORMATION
    output += "\n" + "=" * 80 + "\n"
    output += "DETAILED SERVER INFORMATION\n"
    output += "=" * 80 + "\n"
    
    for info in server_infos:
        # Get the actual hostname from system_info if available, otherwise use IP
        system_hostname = info.info.get('system_info', {}).get('hostname', 'N/A')
        
        # Include hostname, IP and port in server header
        if system_hostname and system_hostname != 'N/A':
            server_header = f"### Server: {system_hostname} ({info.hostname}:{info.port}) ###"
        else:
            server_header = f"### Server: {info.hostname}:{info.port} ###"
        
        if not info.is_available:
            output += f"\n\n{server_header} - UNAVAILABLE\n"
            output += f"Error: {info.error_message}\n"
            continue
            
        output += f"\n\n{server_header}\n"
        
        # System information
        sys_info = info.info.get('system_info', {})
        output += "\n--- System Information ---\n"
        output += f"Hostname: {sys_info.get('hostname', 'N/A')}\n"
        output += f"OS: {sys_info.get('os', 'N/A')}\n"
        output += f"Kernel: {sys_info.get('kernel', 'N/A')}\n"
        output += f"Uptime: {sys_info.get('uptime', 'N/A')}\n"
        
        # Resource information
        resources = info.info.get('resources', {})
        output += "\n--- Resources ---\n"
        
        # CPU information with load average
        output += f"CPU current load: {resources.get('cpu_usage_current', 'N/A')}%\n"
        
        cpu_load = resources.get('cpu_load', {})
        if cpu_load:
            output += "Load Average:\n"
            output += f"  1 min: {cpu_load.get('load_1m', 'N/A')}\n"
            output += f"  5 min: {cpu_load.get('load_5m', 'N/A')}\n"
            output += f" 15 min: {cpu_load.get('load_15m', 'N/A')}\n"
        
        cpu_load_relative = resources.get('cpu_load_relative', {})
        if cpu_load_relative:
            output += "Relative CPU load (% of available cores):\n"
            output += f"  1 min: {cpu_load_relative.get('load_1m_percent', 'N/A')}%\n"
            output += f"  5 min: {cpu_load_relative.get('load_5m_percent', 'N/A')}%\n"
            output += f" 15 min: {cpu_load_relative.get('load_15m_percent', 'N/A')}%\n"
            
        output += f"Number of cores: {resources.get('cpu_cores', 'N/A')}\n"
        
        memory = resources.get('memory', {})
        if memory:
            output += "Memory:\n"
            output += f"  Total: {info.format_bytes(memory.get('total', 0))}\n"
            output += f"  Used: {info.format_bytes(memory.get('used', 0))} ({memory.get('usage_percent', 'N/A')}%)\n"
            output += f"  Free: {info.format_bytes(memory.get('free', 0))}\n"
        
        # All Disks Information
        disks = resources.get('disks', {})
        if disks:
            output += "\n--- Disk Information ---\n"
            
            # Create table for disks
            disk_table = PrettyTable()
            disk_table.field_names = ["Mount Point", "Device", "Total", "Used", "Free", "Usage %"]
            disk_table.align = "l"  # Left alignment
            
            # Add all disks to the table
            for mount_point, disk_info in disks.items():
                disk_table.add_row([
                    disk_info.get('mount_point', 'N/A'),
                    disk_info.get('device', 'N/A'),
                    info.format_bytes(disk_info.get('total', 0)),
                    info.format_bytes(disk_info.get('used', 0)),
                    info.format_bytes(disk_info.get('free', 0)),
                    f"{disk_info.get('usage_percent', 0):.2f}%"
                ])
            
            output += str(disk_table) + "\n"
        else:
            # Legacy format - single disk info
            disk = resources.get('disk', {})
            if disk:
                output += "Disk (/):\n"
                output += f"  Total: {info.format_bytes(disk.get('total', 0))}\n"
                output += f"  Used: {info.format_bytes(disk.get('used', 0))} ({disk.get('usage_percent', 'N/A')}%)\n"
                output += f"  Free: {info.format_bytes(disk.get('free', 0))}\n"
        
        # Docker information (basic)
        docker = info.info.get('docker', {})
        if not docker.get('installed', False):
            output += "\n--- Docker ---\n"
            output += "Docker is not installed\n"
            continue
            
        output += "\n--- Docker ---\n"
        output += f"Version: {docker.get('version', 'N/A')}\n"
        
        docker_info = docker.get('info', {})
        output += f"Running containers: {docker_info.get('containers_running', 'N/A')}\n"
        output += f"Total containers: {docker_info.get('containers_total', 'N/A')}\n"
        output += f"Images: {docker_info.get('images', 'N/A')}\n"
        output += f"Storage Driver: {docker_info.get('storage_driver', 'N/A')}\n"
        output += f"Cgroup Driver: {docker_info.get('cgroup_driver', 'N/A')}\n"
    
    # 3. RUNNING CONTAINERS SECTION
    output += "\n" + "=" * 80 + "\n"
    output += "RUNNING CONTAINERS\n"
    output += "=" * 80 + "\n"
    
    for info in server_infos:
        if not info.is_available:
            continue
        
        docker = info.info.get('docker', {})
        if not docker.get('installed', False):
            continue
        
        # Get the actual hostname from system_info if available, otherwise use IP
        system_hostname = info.info.get('system_info', {}).get('hostname', 'N/A')
        
        # Include hostname, IP and port in server header
        if system_hostname and system_hostname != 'N/A':
            server_header = f"### Server: {system_hostname} ({info.hostname}:{info.port}) ###"
        else:
            server_header = f"### Server: {info.hostname}:{info.port} ###"
            
        containers = docker.get('containers', {}).get('running', [])
        if containers:
            output += f"\n\n{server_header}\n"
            
            # Create table for containers
            container_table = PrettyTable()
            container_table.field_names = ["Name", "Image", "Status", "CPU %", "Memory"]
            container_table.align = "l"  # Left alignment
            container_table.max_width = 30  # Column width limit
            
            for container in containers:
                name = container.get('Names', 'N/A')
                image = container.get('Image', 'N/A')
                status = container.get('Status', 'N/A')
                
                stats = container.get('stats', {})
                cpu_percent = stats.get('CPUPerc', 'N/A')
                mem_usage = stats.get('MemUsage', 'N/A')
                
                container_table.add_row([name, image, status, cpu_percent, mem_usage])
            
            output += str(container_table) + "\n"
        else:
            output += f"\n\n{server_header}\n"
            output += "No running containers\n"

    # 4. DOCKER IMAGES SECTION
    output += "\n" + "=" * 80 + "\n"
    output += "DOCKER IMAGES\n"
    output += "=" * 80 + "\n"
    
    for info in server_infos:
        if not info.is_available:
            continue
        
        docker = info.info.get('docker', {})
        if not docker.get('installed', False):
            continue
        
        # Get the actual hostname from system_info if available, otherwise use IP
        system_hostname = info.info.get('system_info', {}).get('hostname', 'N/A')
        
        # Include hostname, IP and port in server header
        if system_hostname and system_hostname != 'N/A':
            server_header = f"### Server: {system_hostname} ({info.hostname}:{info.port}) ###"
        else:
            server_header = f"### Server: {info.hostname}:{info.port} ###"
            
        images = docker.get('images', [])
        if images:
            output += f"\n\n{server_header}\n"
            
            # Create table for images
            image_table = PrettyTable()
            image_table.field_names = ["Repository", "Tag", "ID", "Size"]
            image_table.align = "l"  # Left alignment
            image_table.max_width = 40  # Column width limit
            
            shown_images = images[:10]  # Show only first 10 images
            for image in shown_images:
                repo = image.get('Repository', 'N/A')
                tag = image.get('Tag', 'N/A')
                image_id = image.get('ID', 'N/A')
                size = image.get('Size', 'N/A')
                
                image_table.add_row([repo, tag, image_id, size])
            
            output += str(image_table) + "\n"
            
            if len(images) > 10:
                output += f"...and {len(images) - 10} more images...\n"
        else:
            output += f"\n\n{server_header}\n"
            output += "No Docker images\n"
    
    # Print and save results
    print(output)
    
    # Write to file, if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
            
        print(f"\nResults saved to file: {output_file}")

def format_json_output(server_infos, output_file=None):
    """Formatting output in JSON format."""
    result = json.dumps({
        'timestamp': datetime.datetime.now().isoformat(),
        'servers': [info.info for info in server_infos]
    }, indent=2)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(result)
        print(f"\nResults saved to file: {output_file}")
    else:
        print(result)

def format_csv_output(server_infos, output_file=None):
    """Formatting output in CSV format."""
    headers = ['hostname', 'port', 'status', 'cpu_usage', 'cpu_load_1m', 'cpu_load_5m', 'cpu_load_15m', 
              'cpu_load_relative', 'cpu_cores', 'memory_usage', 'memory_percent', 
              'disk_usage', 'disk_percent', 'containers_running', 'containers_total']
    
    # Get summary information about each server
    summaries = [info.get_summary() for info in server_infos]
    
    csv_content = ','.join(headers) + '\n'
    
    for summary in summaries:
        row = [str(summary.get(header, '')) for header in headers]
        csv_content += ','.join(row) + '\n'
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(csv_content)
        print(f"\nResults saved to file: {output_file}")
    else:
        print(csv_content)

def format_output(server_infos, output_format, output_file=None):
    """Formatting and output of results in chosen format."""
    if output_format == 'json':
        format_json_output(server_infos, output_file)
    elif output_format == 'csv':
        format_csv_output(server_infos, output_file)
    else:  # 'text' by default
        format_text_output(server_infos, output_file)