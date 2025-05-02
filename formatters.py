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
    table.field_names = ["Server", "Port", "Status", "CPU (curr.)", "Load Avg (5m)", "Cores", "Memory", "Disk", "Cont. (act)", "Cont. (total)"]
    
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
    
    # Detailed information about each server
    detailed_info = ""
    for info in server_infos:
        if not info.is_available:
            detailed_info += f"\n\n### Server: {info.hostname} - UNAVAILABLE ###\n"
            detailed_info += f"Error: {info.error_message}\n"
            continue
            
        detailed_info += f"\n\n### Server: {info.hostname} ###\n"
        
        # System information
        sys_info = info.info.get('system_info', {})
        detailed_info += "\n--- System Information ---\n"
        detailed_info += f"OS: {sys_info.get('os', 'N/A')}\n"
        detailed_info += f"Kernel: {sys_info.get('kernel', 'N/A')}\n"
        detailed_info += f"Uptime: {sys_info.get('uptime', 'N/A')}\n"
        
        # Resource information
        resources = info.info.get('resources', {})
        detailed_info += "\n--- Resources ---\n"
        
        # CPU information with load average
        detailed_info += f"CPU current load: {resources.get('cpu_usage_current', 'N/A')}%\n"
        
        cpu_load = resources.get('cpu_load', {})
        if cpu_load:
            detailed_info += "Load Average:\n"
            detailed_info += f"  1 min: {cpu_load.get('load_1m', 'N/A')}\n"
            detailed_info += f"  5 min: {cpu_load.get('load_5m', 'N/A')}\n"
            detailed_info += f" 15 min: {cpu_load.get('load_15m', 'N/A')}\n"
        
        cpu_load_relative = resources.get('cpu_load_relative', {})
        if cpu_load_relative:
            detailed_info += "Relative CPU load (% of available cores):\n"
            detailed_info += f"  1 min: {cpu_load_relative.get('load_1m_percent', 'N/A')}%\n"
            detailed_info += f"  5 min: {cpu_load_relative.get('load_5m_percent', 'N/A')}%\n"
            detailed_info += f" 15 min: {cpu_load_relative.get('load_15m_percent', 'N/A')}%\n"
            
        detailed_info += f"Number of cores: {resources.get('cpu_cores', 'N/A')}\n"
        
        memory = resources.get('memory', {})
        if memory:
            detailed_info += "Memory:\n"
            detailed_info += f"  Total: {info.format_bytes(memory.get('total', 0))}\n"
            detailed_info += f"  Used: {info.format_bytes(memory.get('used', 0))} ({memory.get('usage_percent', 'N/A')}%)\n"
            detailed_info += f"  Free: {info.format_bytes(memory.get('free', 0))}\n"
        
        disk = resources.get('disk', {})
        if disk:
            detailed_info += "Disk (/):\n"
            detailed_info += f"  Total: {info.format_bytes(disk.get('total', 0))}\n"
            detailed_info += f"  Used: {info.format_bytes(disk.get('used', 0))} ({disk.get('usage_percent', 'N/A')}%)\n"
            detailed_info += f"  Free: {info.format_bytes(disk.get('free', 0))}\n"
        
        # Docker information
        docker = info.info.get('docker', {})
        if not docker.get('installed', False):
            detailed_info += "\n--- Docker ---\n"
            detailed_info += "Docker is not installed\n"
            continue
            
        detailed_info += "\n--- Docker ---\n"
        detailed_info += f"Version: {docker.get('version', 'N/A')}\n"
        
        docker_info = docker.get('info', {})
        detailed_info += f"Running containers: {docker_info.get('containers_running', 'N/A')}\n"
        detailed_info += f"Total containers: {docker_info.get('containers_total', 'N/A')}\n"
        detailed_info += f"Images: {docker_info.get('images', 'N/A')}\n"
        detailed_info += f"Storage Driver: {docker_info.get('storage_driver', 'N/A')}\n"
        detailed_info += f"Cgroup Driver: {docker_info.get('cgroup_driver', 'N/A')}\n"
        
        # List of running containers
        containers = docker.get('containers', {}).get('running', [])
        if containers:
            detailed_info += "\n--- Running Containers ---\n"
            
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
            
            detailed_info += str(container_table) + "\n"
        
        # List of images
        images = docker.get('images', [])
        if images:
            detailed_info += "\n--- Docker Images ---\n"
            
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
            
            detailed_info += str(image_table) + "\n"
            
            if len(images) > 10:
                detailed_info += f"...and {len(images) - 10} more images...\n"
    
    # Output results
    print("\n" + "=" * 80)
    print("SERVER SUMMARY")
    print("=" * 80)
    print(table)
    
    print("\n" + "=" * 80)
    print("DETAILED SERVER INFORMATION")
    print("=" * 80)
    print(detailed_info)
    
    # Write to file, if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write("SERVER SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(str(table) + "\n\n")
            
            f.write("DETAILED SERVER INFORMATION\n")
            f.write("=" * 80 + "\n")
            f.write(detailed_info)
            
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