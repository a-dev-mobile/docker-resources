# Docker Resources

A tool for monitoring Docker resources and containers on remote servers. It allows you to collect information from multiple servers simultaneously and present it in various formats.

## Features

- Parallel connection to servers
- Collection of system, resource, and Docker container information
- Detailed analysis of resource usage by each container
- Output in various formats (text, JSON, CSV)
- Saving results to a file

## Requirements

On the local computer:
- Python 3.6 or higher
- Libraries: paramiko, prettytable

On remote servers:
- SSH server
- Docker
- Recommended (but not required): jq utility for JSON formatting

## Installation

### From source code

```bash
# Clone repository
git clone <repository_url>
cd docker-resources

# Install dependencies
pip install -r requirements.txt

# Install package (optional)
pip install -e .
```

### Using pip

```bash
pip install docker-resources
```

## Usage

### Preparation

Create a `servers.txt` file with a list of servers:

```
user@server1
user@server2
user@server3:2222  # Specifying non-standard SSH port
admin@server4:2233  # Different user and port
```

### Running

```bash
# Basic usage
python -m docker_resources

# Specifying servers file and SSH key
python -m docker_resources -f my_servers.txt -k ~/.ssh/id_rsa

# Specifying output format and output filename
python -m docker_resources --format json -o results.json
```

### Command-line parameters

- `-f, --file` - path to the file with server list (default: servers.txt)
- `-o, --output` - file to save results
- `-k, --key` - SSH private key file
- `--format` - output format (text, json, csv)

## Examples

```bash
# Save report in CSV format
python -m docker_resources --format csv -o servers_report.csv

# Use with specific SSH key and JSON output
python -m docker_resources -k ~/.ssh/server_key -f production_servers.txt --format json
```

## Tips for Debian

If the `jq` utility is not installed on remote servers, the script will use alternative methods. However, for better support it is recommended to install it:

```bash
apt-get update && apt-get install -y jq
```

## License

MIT