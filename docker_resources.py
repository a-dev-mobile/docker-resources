#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для сбора информации о ресурсах Docker на удаленных серверах.
"""

import os
import sys
import time
import datetime
import argparse
from concurrent.futures import ThreadPoolExecutor

from server_info import ServerInfo
from formatters import format_output

# Настройки по умолчанию
DEFAULT_SERVERS_FILE = "servers.txt"
DEFAULT_OUTPUT_FORMAT = "text"
DEFAULT_TIMEOUT = 5  # Таймаут подключения к серверу в секундах
MAX_WORKERS = 10  # Максимальное количество параллельных подключений

def read_servers_file(file_path):
    """Чтение файла со списком серверов."""
    servers = []
    
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл {file_path} не найден.")
        print("Создайте файл в формате: user@hostname или hostname (по одному на строку)")
        sys.exit(1)
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                servers.append(line)
    
    return servers

def process_server(server_address, key_file=None):
    """Обработка одного сервера."""
    print(f"Проверка сервера: {server_address}...")
    server_info = ServerInfo(server_address, key_file=key_file)
    success = server_info.collect_all_info()
    
    if success:
        print(f"Сбор информации для {server_address} завершен успешно.")
    else:
        print(f"Ошибка при сборе информации для {server_address}: {server_info.error_message}")
        
    return server_info

def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(description='Скрипт для проверки ресурсов Docker на серверах.')
    parser.add_argument('-f', '--file', help='Файл со списком серверов', default=DEFAULT_SERVERS_FILE)
    parser.add_argument('-o', '--output', help='Файл для записи результатов')
    parser.add_argument('-k', '--key', help='Файл приватного ключа для SSH')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default=DEFAULT_OUTPUT_FORMAT,
                        help='Формат вывода результатов')
    args = parser.parse_args()
    
    # Чтение списка серверов
    servers = read_servers_file(args.file)
    print(f"Найдено {len(servers)} серверов для проверки.")
    
    # Используем ThreadPoolExecutor для параллельной обработки серверов
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
                print(f"Ошибка при обработке сервера {futures[future]}: {str(e)}")
    
    # Форматирование и вывод результатов
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output or f"docker_resources_{timestamp}.{args.format}"
    
    format_output(server_infos, args.format, output_file)

if __name__ == "__main__":
    main()