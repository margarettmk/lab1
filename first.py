import sys
import os
import json
import socket
import platform
import shutil
import time
import locale
from datetime import datetime
from pathlib import Path


def detect_os():
    """Определяет операционную систему."""
    if sys.platform.startswith("win"):
        return "Windows"
    elif sys.platform.startswith("linux"):
        return "Linux"
    elif sys.platform == "darwin":
        return "macOS"
    else:
        return "Unknown"


def bytes_to_gb(value):
    """Переводит байты в гигабайты."""
    return round(value / (1024 ** 3), 2)


def get_memory_size():
    """
    Определяет общий объём оперативной памяти.
    Используются только средства стандартной библиотеки Python.
    """
    system = detect_os()

    try:
        # Windows
        if system == "Windows":
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)
                ]

            memory_status = MemoryStatus()
            memory_status.dwLength = ctypes.sizeof(MemoryStatus)

            ctypes.windll.kernel32.GlobalMemoryStatusEx(
                ctypes.byref(memory_status)
            )

            return bytes_to_gb(memory_status.ullTotalPhys)

        # Linux и macOS
        elif system in ("Linux", "macOS"):
            page_size = os.sysconf("SC_PAGE_SIZE")
            pages = os.sysconf("SC_PHYS_PAGES")

            return bytes_to_gb(page_size * pages)

    except (OSError, ValueError, AttributeError):
        return None

    return None


def get_linux_distribution():
    """
    Получает название дистрибутива Linux из /etc/os-release.
    Файл читается напрямую, системные команды не запускаются.
    """
    os_release = Path("/etc/os-release")

    if not os_release.exists():
        return None

    information = {}

    try:
        with open(os_release, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if "=" in line:
                    key, value = line.split("=", 1)
                    information[key] = value.strip('"')

        return information.get("PRETTY_NAME")

    except OSError:
        return None


def get_os_version():
    """Получает сведения о версии конкретной ОС."""
    system = detect_os()

    if system == "Windows":
        version = sys.getwindowsversion()

        return {
            "major": version.major,
            "minor": version.minor,
            "build": version.build,
            "service_pack": version.service_pack
        }

    elif system == "Linux":
        uname = os.uname()

        return {
            "distribution": get_linux_distribution(),
            "kernel_release": uname.release,
            "kernel_version": uname.version
        }

    elif system == "macOS":
        uname = os.uname()

        return {
            "macos_version": platform.mac_ver()[0],
            "kernel_release": uname.release
        }

    return {}


def get_disk_info():
    """Получает сведения о диске, на котором находится домашняя папка."""
    system = detect_os()

    if system == "Windows":
        root = Path.home().anchor
    else:
        root = "/"

    total, used, free = shutil.disk_usage(root)

    return {
        "path": root,
        "total_gb": bytes_to_gb(total),
        "used_gb": bytes_to_gb(used),
        "free_gb": bytes_to_gb(free)
    }


def collect_system_info():
    """Собирает информацию о текущей системе."""

    system = detect_os()

    data = {
        "collection_time": datetime.now().astimezone().isoformat(),

        "operating_system": {
            "name": system,
            "platform": sys.platform,
            "os_name": os.name,
            "version": get_os_version()
        },

        "computer": {
            "hostname": socket.gethostname(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(),
            "ram_gb": get_memory_size()
        },

        "disk": get_disk_info(),

        "environment": {
            "timezone": time.tzname[0],
            "encoding": locale.getencoding()
        },

        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable
        }
    }

    return data


def save_to_json(data):
    """Записывает информацию в JSON-файл."""

    output_file = Path(__file__).with_name("os_info.json")

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )

    return output_file


def main():
    print("Сбор информации о системе...")

    system_info = collect_system_info()

    output_file = save_to_json(system_info)

    print(f"Операционная система: "
          f"{system_info['operating_system']['name']}")

    print(f"Результат записан в файл: {output_file}")


if __name__ == "__main__":
    main()