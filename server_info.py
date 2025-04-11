#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для сбора информации о серверах через SSH.
"""

import os
import json
import socket
import paramiko

class ServerInfo:
    """Класс для сбора и хранения информации о сервере."""
    
    def __init__(self, hostname, username=None, port=22, key_file=None, password=None):
        """Инициализация с параметрами подключения."""
        # Обработка формата user@hostname:port
        if '@' in hostname:
            parts = hostname.split('@')
            username_part = parts[0]
            host_part = parts[1]
            
            # Проверка наличия порта
            if ':' in host_part:
                host_parts = host_part.split(':')
                self.hostname = host_parts[0]
                self.port = int(host_parts[1])
            else:
                self.hostname = host_part
                self.port = port
                
            self.username = username_part
        else:
            # Проверка наличия порта без имени пользователя
            if ':' in hostname:
                host_parts = hostname.split(':')
                self.hostname = host_parts[0]
                self.port = int(host_parts[1])
            else:
                self.hostname = hostname
                self.port = port
                
            self.username = username
            
        self.key_file = key_file
        self.password = password
        self.is_available = False
        self.error_message = None
        self.info = {
            'hostname': self.hostname,
            'port': self.port,
            'system_info': {},
            'resources': {},
            'docker': {
                'installed': False,
                'version': None,
                'info': {},
                'containers': {
                    'running': [],
                    'all': []
                },
                'images': []
            }
        }
        
    def connect(self):
        """Установка SSH-соединения с сервером."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_args = {
                'hostname': self.hostname,
                'port': self.port,
                'timeout': 5  # DEFAULT_TIMEOUT
            }
            
            if self.username:
                connect_args['username'] = self.username
                
            if self.key_file:
                if os.path.exists(os.path.expanduser(self.key_file)):
                    connect_args['key_filename'] = os.path.expanduser(self.key_file)
            
            if self.password:
                connect_args['password'] = self.password
                
            self.client.connect(**connect_args)
            self.is_available = True
            return True
        except socket.timeout:
            self.error_message = "Таймаут подключения"
            return False
        except paramiko.AuthenticationException:
            self.error_message = "Ошибка аутентификации"
            return False
        except paramiko.SSHException as e:
            self.error_message = f"Ошибка SSH: {str(e)}"
            return False
        except Exception as e:
            self.error_message = f"Ошибка подключения: {str(e)}"
            return False
    
    def disconnect(self):
        """Закрытие SSH-соединения."""
        if hasattr(self, 'client'):
            self.client.close()
    
    def execute_command(self, command):
        """Выполнение команды на сервере и возврат результата."""
        if not self.is_available:
            return None, f"Сервер недоступен: {self.error_message}"
            
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=5)
            exit_status = stdout.channel.recv_exit_status()  # Дожидаемся завершения команды
            
            output = stdout.read().decode('utf-8', errors='replace').strip()
            error = stderr.read().decode('utf-8', errors='replace').strip()
            
            if exit_status != 0:
                if error:
                    return None, f"Команда завершилась с ошибкой (код {exit_status}): {error}"
                else:
                    return None, f"Команда завершилась с ошибкой (код {exit_status})"
            
            if error and not output:
                return None, error
            
            return output, error
        except Exception as e:
            return None, f"Ошибка выполнения команды '{command}': {str(e)}"
    
    def collect_system_info(self):
        """Сбор общей информации о системе."""
        if not self.is_available:
            return
            
        # Получение имени хоста
        output, _ = self.execute_command("hostname")
        if output:
            self.info['system_info']['hostname'] = output
            
        # Получение информации об ОС
        output, _ = self.execute_command("cat /etc/os-release | grep PRETTY_NAME | cut -d '\"' -f 2")
        if output:
            self.info['system_info']['os'] = output
            
        # Получение версии ядра
        output, _ = self.execute_command("uname -r")
        if output:
            self.info['system_info']['kernel'] = output
            
        # Получение времени работы системы
        output, _ = self.execute_command("uptime -p")
        if output:
            self.info['system_info']['uptime'] = output
    
    def collect_resource_info(self):
        """Сбор информации о ресурсах."""
        if not self.is_available:
            return
            
        # Более точная информация о CPU - средняя нагрузка за 1, 5 и 15 минут
        output, _ = self.execute_command("cat /proc/loadavg")
        if output:
            parts = output.split()
            if len(parts) >= 3:
                self.info['resources']['cpu_load'] = {
                    'load_1m': float(parts[0]),
                    'load_5m': float(parts[1]),
                    'load_15m': float(parts[2])
                }
            
        # Текущая загрузка CPU (моментальный снимок)
        output, _ = self.execute_command("top -bn1 | grep 'Cpu(s)'")
        if output:
            # Парсим вывод top для получения загрузки CPU
            parts = output.split(',')
            user_cpu = float(parts[0].split()[1])
            system_cpu = float(parts[1].split()[0])
            self.info['resources']['cpu_usage_current'] = round(user_cpu + system_cpu, 2)
            
        # Количество ядер CPU
        output, _ = self.execute_command("nproc")
        if output:
            self.info['resources']['cpu_cores'] = int(output)
            
            # Расчет относительной нагрузки (load average / количество ядер)
            if 'cpu_load' in self.info['resources']:
                cores = self.info['resources']['cpu_cores']
                self.info['resources']['cpu_load_relative'] = {
                    'load_1m_percent': round((self.info['resources']['cpu_load']['load_1m'] / cores) * 100, 2),
                    'load_5m_percent': round((self.info['resources']['cpu_load']['load_5m'] / cores) * 100, 2),
                    'load_15m_percent': round((self.info['resources']['cpu_load']['load_15m'] / cores) * 100, 2)
                }
            
        # Информация о памяти
        output, _ = self.execute_command("free -b")
        if output:
            lines = output.strip().split('\n')
            if len(lines) > 1:
                mem_parts = lines[1].split()
                if len(mem_parts) >= 7:
                    total_mem = int(mem_parts[1])
                    used_mem = int(mem_parts[2])
                    self.info['resources']['memory'] = {
                        'total': total_mem,
                        'used': used_mem,
                        'free': total_mem - used_mem,
                        'usage_percent': round((used_mem / total_mem) * 100, 2)
                    }
        
        # Информация о диске
        output, _ = self.execute_command("df -B1 / | tail -1")
        if output:
            parts = output.split()
            if len(parts) >= 6:
                total_disk = int(parts[1])
                used_disk = int(parts[2])
                avail_disk = int(parts[3])
                self.info['resources']['disk'] = {
                    'total': total_disk,
                    'used': used_disk,
                    'free': avail_disk,
                    'usage_percent': round((used_disk / total_disk) * 100, 2)
                }
    
    def collect_docker_info(self):
        """Сбор информации о Docker и контейнерах."""
        if not self.is_available:
            return
            
        # Проверка наличия Docker
        output, _ = self.execute_command("command -v docker")
        if not output:
            self.info['docker']['installed'] = False
            return
            
        self.info['docker']['installed'] = True
        
        # Получение версии Docker
        output, _ = self.execute_command("docker --version")
        if output:
            self.info['docker']['version'] = output
            
        # Получение информации о Docker демоне
        output, _ = self.execute_command("docker info --format '{{json .}}'")
        if output:
            try:
                docker_info = json.loads(output)
                self.info['docker']['info'] = {
                    'containers_running': docker_info.get('ContainersRunning', 0),
                    'containers_total': docker_info.get('Containers', 0),
                    'images': docker_info.get('Images', 0),
                    'storage_driver': docker_info.get('Driver', ''),
                    'cgroup_driver': docker_info.get('CgroupDriver', '')
                }
            except json.JSONDecodeError as e:
                print(f"Ошибка при парсинге JSON информации о Docker на {self.hostname}: {str(e)}")
                # Установка значений по умолчанию
                self.info['docker']['info'] = {
                    'containers_running': 0,
                    'containers_total': 0,
                    'images': 0,
                    'storage_driver': 'неизвестно',
                    'cgroup_driver': 'неизвестно'
                }
        
        # Проверка наличия jq для парсинга JSON
        has_jq, _ = self.execute_command("command -v jq")
        
        # Получение списка запущенных контейнеров с использованием ресурсов
        if has_jq:
            output, _ = self.execute_command("""
                docker ps --format '{{json .}}' | jq -s '.'
            """)
        else:
            # Альтернативный метод без jq
            output, _ = self.execute_command("""
                echo "["
                docker ps --format '{{json .}}' | sed -e 's/$/,/'
                echo "{}"
                echo "]"
            """)
            # Исправление JSON-формата (убираем лишнюю запятую)
            if output:
                output = output.replace(",\n{}\n]", "\n]")
        
        if output and output != "null":
            try:
                containers = json.loads(output)
                for container in containers:
                    container_name = container.get('Names', '')
                    # Получение использования ресурсов для контейнера
                    stats_output, _ = self.execute_command(f"""
                        docker stats {container_name} --no-stream --format '{{{{json .}}}}'
                    """)
                    
                    if stats_output:
                        try:
                            stats = json.loads(stats_output)
                            container['stats'] = stats
                        except json.JSONDecodeError:
                            container['stats'] = {}
                    
                    # Получение лимитов ресурсов для контейнера
                    inspect_output, _ = self.execute_command(f"""
                        docker inspect {container_name} --format '{{{{json .HostConfig}}}}'
                    """)
                    
                    if inspect_output:
                        try:
                            host_config = json.loads(inspect_output)
                            container['limits'] = {
                                'cpu': host_config.get('CpuShares', 0),
                                'memory': host_config.get('Memory', 0)
                            }
                        except json.JSONDecodeError:
                            container['limits'] = {}
                            
                    self.info['docker']['containers']['running'].append(container)
            except json.JSONDecodeError:
                pass
            
        # Получение списка всех контейнеров
        if has_jq:
            output, _ = self.execute_command("""
                docker ps -a --format '{{json .}}' | jq -s '.'
            """)
        else:
            # Альтернативный метод без jq
            output, _ = self.execute_command("""
                echo "["
                docker ps -a --format '{{json .}}' | sed -e 's/$/,/'
                echo "{}"
                echo "]"
            """)
            # Исправление JSON-формата (убираем лишнюю запятую)
            if output:
                output = output.replace(",\n{}\n]", "\n]")
        
        if output and output != "null":
            try:
                self.info['docker']['containers']['all'] = json.loads(output)
            except json.JSONDecodeError:
                pass
            
        # Получение списка образов
        if has_jq:
            output, _ = self.execute_command("""
                docker images --format '{{json .}}' | jq -s '.'
            """)
        else:
            # Альтернативный метод без jq
            output, _ = self.execute_command("""
                echo "["
                docker images --format '{{json .}}' | sed -e 's/$/,/'
                echo "{}"
                echo "]"
            """)
            # Исправление JSON-формата (убираем лишнюю запятую)
            if output:
                output = output.replace(",\n{}\n]", "\n]")
        
        if output and output != "null":
            try:
                self.info['docker']['images'] = json.loads(output)
            except json.JSONDecodeError:
                pass
    
    def collect_all_info(self):
        """Сбор всей информации о сервере."""
        if not self.connect():
            return False
            
        try:
            self.collect_system_info()
            self.collect_resource_info()
            self.collect_docker_info()
            return True
        finally:
            self.disconnect()
    
    def format_bytes(self, size_bytes):
        """Преобразование байтов в человеко-читаемый формат."""
        if size_bytes == 0 or size_bytes is None:
            return "0B"
        
        # Преобразуем в число, если передана строка
        if isinstance(size_bytes, str):
            try:
                size_bytes = float(size_bytes)
            except (ValueError, TypeError):
                return size_bytes  # Возвращаем как есть, если не можем преобразовать
        
        size_names = ("B", "KB", "MB", "GB", "TB", "PB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        # Округление до 2 знаков после запятой
        return f"{round(size_bytes, 2)}{size_names[i]}"
    
    def get_summary(self):
        """Получение сводной информации о сервере."""
        if not self.is_available:
            return {
                'hostname': self.hostname,
                'port': self.port,
                'status': 'недоступен',
                'error': self.error_message,
                'cpu_usage': 'N/A',
                'memory_usage': 'N/A',
                'disk_usage': 'N/A',
                'containers_running': 'N/A',
                'containers_total': 'N/A'
            }
            
        memory = self.info.get('resources', {}).get('memory', {})
        memory_usage = f"{self.format_bytes(memory.get('used', 0))}/{self.format_bytes(memory.get('total', 0))}"
        memory_percent = memory.get('usage_percent', 0)
        if isinstance(memory_percent, (int, float)):
            memory_percent = f"{memory_percent:.2f}%"
        else:
            memory_percent = f"{memory_percent}%"
        
        disk = self.info.get('resources', {}).get('disk', {})
        disk_usage = f"{self.format_bytes(disk.get('used', 0))}/{self.format_bytes(disk.get('total', 0))}"
        disk_percent = disk.get('usage_percent', 0)
        if isinstance(disk_percent, (int, float)):
            disk_percent = f"{disk_percent:.2f}%"
        else:
            disk_percent = f"{disk_percent}%"
        
        docker_info = self.info.get('docker', {}).get('info', {})
        
        # Форматирование CPU-загрузки
        cpu_usage = self.info.get('resources', {}).get('cpu_usage_current', 0)
        if isinstance(cpu_usage, (int, float)):
            cpu_usage_str = f"{cpu_usage:.1f}%"
        else:
            cpu_usage_str = f"{cpu_usage}%"
        
        # Форматирование Load Average
        cpu_load_relative = self.info.get('resources', {}).get('cpu_load_relative', {}).get('load_5m_percent', 0)
        if isinstance(cpu_load_relative, (int, float)):
            cpu_load_str = f"{cpu_load_relative:.2f}%"
        else:
            cpu_load_str = f"{cpu_load_relative}%"
        
        return {
            'hostname': self.hostname,
            'port': self.port,
            'status': 'доступен',
            'cpu_usage': cpu_usage_str,
            'cpu_load_1m': self.info.get('resources', {}).get('cpu_load', {}).get('load_1m', 'N/A'),
            'cpu_load_5m': self.info.get('resources', {}).get('cpu_load', {}).get('load_5m', 'N/A'),
            'cpu_load_15m': self.info.get('resources', {}).get('cpu_load', {}).get('load_15m', 'N/A'),
            'cpu_load_relative': cpu_load_str,
            'cpu_cores': self.info.get('resources', {}).get('cpu_cores', 'N/A'),
            'memory_usage': memory_usage,
            'memory_percent': memory_percent,
            'disk_usage': disk_usage,
            'disk_percent': disk_percent,
            'containers_running': docker_info.get('containers_running', 0),
            'containers_total': docker_info.get('containers_total', 0)
        }