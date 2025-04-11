#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для форматирования вывода информации о серверах.
"""

import json
import datetime
from prettytable import PrettyTable

def format_text_output(server_infos, output_file=None):
    """Форматирование вывода в текстовом формате."""
    # Создаем таблицу для сводки
    table = PrettyTable()
    table.field_names = ["Сервер", "Порт", "Статус", "CPU (тек.)", "Load Avg (5м)", "Ядра", "Память", "Диск", "Конт. (акт)", "Конт. (всего)"]
    
    # Получаем сводную информацию о каждом сервере
    summaries = [info.get_summary() for info in server_infos]
    
    for summary in summaries:
        if summary['status'] == 'доступен':
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
    
    # Подробная информация о каждом сервере
    detailed_info = ""
    for info in server_infos:
        if not info.is_available:
            detailed_info += f"\n\n### Сервер: {info.hostname} - НЕДОСТУПЕН ###\n"
            detailed_info += f"Ошибка: {info.error_message}\n"
            continue
            
        detailed_info += f"\n\n### Сервер: {info.hostname} ###\n"
        
        # Информация о системе
        sys_info = info.info.get('system_info', {})
        detailed_info += "\n--- Системная информация ---\n"
        detailed_info += f"ОС: {sys_info.get('os', 'Н/Д')}\n"
        detailed_info += f"Ядро: {sys_info.get('kernel', 'Н/Д')}\n"
        detailed_info += f"Время работы: {sys_info.get('uptime', 'Н/Д')}\n"
        
        # Информация о ресурсах
        resources = info.info.get('resources', {})
        detailed_info += "\n--- Ресурсы ---\n"
        
        # CPU информация с load average
        detailed_info += f"CPU текущая загрузка: {resources.get('cpu_usage_current', 'Н/Д')}%\n"
        
        cpu_load = resources.get('cpu_load', {})
        if cpu_load:
            detailed_info += "Load Average:\n"
            detailed_info += f"  1 мин: {cpu_load.get('load_1m', 'Н/Д')}\n"
            detailed_info += f"  5 мин: {cpu_load.get('load_5m', 'Н/Д')}\n"
            detailed_info += f" 15 мин: {cpu_load.get('load_15m', 'Н/Д')}\n"
        
        cpu_load_relative = resources.get('cpu_load_relative', {})
        if cpu_load_relative:
            detailed_info += "Относительная загрузка CPU (% от доступных ядер):\n"
            detailed_info += f"  1 мин: {cpu_load_relative.get('load_1m_percent', 'Н/Д')}%\n"
            detailed_info += f"  5 мин: {cpu_load_relative.get('load_5m_percent', 'Н/Д')}%\n"
            detailed_info += f" 15 мин: {cpu_load_relative.get('load_15m_percent', 'Н/Д')}%\n"
            
        detailed_info += f"Количество ядер: {resources.get('cpu_cores', 'Н/Д')}\n"
        
        memory = resources.get('memory', {})
        if memory:
            detailed_info += "Память:\n"
            detailed_info += f"  Всего: {info.format_bytes(memory.get('total', 0))}\n"
            detailed_info += f"  Используется: {info.format_bytes(memory.get('used', 0))} ({memory.get('usage_percent', 'Н/Д')}%)\n"
            detailed_info += f"  Свободно: {info.format_bytes(memory.get('free', 0))}\n"
        
        disk = resources.get('disk', {})
        if disk:
            detailed_info += "Диск (/):\n"
            detailed_info += f"  Всего: {info.format_bytes(disk.get('total', 0))}\n"
            detailed_info += f"  Используется: {info.format_bytes(disk.get('used', 0))} ({disk.get('usage_percent', 'Н/Д')}%)\n"
            detailed_info += f"  Свободно: {info.format_bytes(disk.get('free', 0))}\n"
        
        # Информация о Docker
        docker = info.info.get('docker', {})
        if not docker.get('installed', False):
            detailed_info += "\n--- Docker ---\n"
            detailed_info += "Docker не установлен\n"
            continue
            
        detailed_info += "\n--- Docker ---\n"
        detailed_info += f"Версия: {docker.get('version', 'Н/Д')}\n"
        
        docker_info = docker.get('info', {})
        detailed_info += f"Контейнеров запущено: {docker_info.get('containers_running', 'Н/Д')}\n"
        detailed_info += f"Контейнеров всего: {docker_info.get('containers_total', 'Н/Д')}\n"
        detailed_info += f"Образов: {docker_info.get('images', 'Н/Д')}\n"
        detailed_info += f"Storage Driver: {docker_info.get('storage_driver', 'Н/Д')}\n"
        detailed_info += f"Cgroup Driver: {docker_info.get('cgroup_driver', 'Н/Д')}\n"
        
        # Список запущенных контейнеров
        containers = docker.get('containers', {}).get('running', [])
        if containers:
            detailed_info += "\n--- Запущенные контейнеры ---\n"
            
            # Создаем таблицу для контейнеров
            container_table = PrettyTable()
            container_table.field_names = ["Имя", "Образ", "Статус", "CPU %", "Память"]
            container_table.align = "l"  # Выравнивание по левому краю
            container_table.max_width = 30  # Ограничение ширины столбцов
            
            for container in containers:
                name = container.get('Names', 'Н/Д')
                image = container.get('Image', 'Н/Д')
                status = container.get('Status', 'Н/Д')
                
                stats = container.get('stats', {})
                cpu_percent = stats.get('CPUPerc', 'Н/Д')
                mem_usage = stats.get('MemUsage', 'Н/Д')
                
                container_table.add_row([name, image, status, cpu_percent, mem_usage])
            
            detailed_info += str(container_table) + "\n"
        
        # Список образов
        images = docker.get('images', [])
        if images:
            detailed_info += "\n--- Образы Docker ---\n"
            
            # Создаем таблицу для образов
            image_table = PrettyTable()
            image_table.field_names = ["Репозиторий", "Тэг", "ID", "Размер"]
            image_table.align = "l"  # Выравнивание по левому краю
            image_table.max_width = 40  # Ограничение ширины столбцов
            
            shown_images = images[:10]  # Показываем только первые 10 образов
            for image in shown_images:
                repo = image.get('Repository', 'Н/Д')
                tag = image.get('Tag', 'Н/Д')
                image_id = image.get('ID', 'Н/Д')
                size = image.get('Size', 'Н/Д')
                
                image_table.add_row([repo, tag, image_id, size])
            
            detailed_info += str(image_table) + "\n"
            
            if len(images) > 10:
                detailed_info += f"...и ещё {len(images) - 10} образов...\n"
    
    # Выводим результаты
    print("\n" + "=" * 80)
    print("СВОДКА ПО СЕРВЕРАМ")
    print("=" * 80)
    print(table)
    
    print("\n" + "=" * 80)
    print("ПОДРОБНАЯ ИНФОРМАЦИЯ ПО СЕРВЕРАМ")
    print("=" * 80)
    print(detailed_info)
    
    # Запись в файл, если указан
    if output_file:
        with open(output_file, 'w') as f:
            f.write("СВОДКА ПО СЕРВЕРАМ\n")
            f.write("=" * 80 + "\n")
            f.write(str(table) + "\n\n")
            
            f.write("ПОДРОБНАЯ ИНФОРМАЦИЯ ПО СЕРВЕРАМ\n")
            f.write("=" * 80 + "\n")
            f.write(detailed_info)
            
        print(f"\nРезультаты сохранены в файл: {output_file}")

def format_json_output(server_infos, output_file=None):
    """Форматирование вывода в JSON формате."""
    result = json.dumps({
        'timestamp': datetime.datetime.now().isoformat(),
        'servers': [info.info for info in server_infos]
    }, indent=2)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(result)
        print(f"\nРезультаты сохранены в файл: {output_file}")
    else:
        print(result)

def format_csv_output(server_infos, output_file=None):
    """Форматирование вывода в CSV формате."""
    headers = ['hostname', 'port', 'status', 'cpu_usage', 'cpu_load_1m', 'cpu_load_5m', 'cpu_load_15m', 
              'cpu_load_relative', 'cpu_cores', 'memory_usage', 'memory_percent', 
              'disk_usage', 'disk_percent', 'containers_running', 'containers_total']
    
    # Получаем сводную информацию о каждом сервере
    summaries = [info.get_summary() for info in server_infos]
    
    csv_content = ','.join(headers) + '\n'
    
    for summary in summaries:
        row = [str(summary.get(header, '')) for header in headers]
        csv_content += ','.join(row) + '\n'
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(csv_content)
        print(f"\nРезультаты сохранены в файл: {output_file}")
    else:
        print(csv_content)

def format_output(server_infos, output_format, output_file=None):
    """Форматирование и вывод результатов в выбранном формате."""
    if output_format == 'json':
        format_json_output(server_infos, output_file)
    elif output_format == 'csv':
        format_csv_output(server_infos, output_file)
    else:  # 'text' по умолчанию
        format_text_output(server_infos, output_file)