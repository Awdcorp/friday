import platform
import psutil
import cpuinfo
import subprocess
import shutil

def bytes_to_gb(n):
    return round(n / (1024 ** 3), 2)

def get_cpu_info():
    info = cpuinfo.get_cpu_info()
    return {
        "brand": info.get("brand_raw", "Unknown"),
        "arch": info.get("arch_string_raw", "Unknown"),
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True)
    }

def get_ram_info():
    virtual_mem = psutil.virtual_memory()
    return {
        "total_gb": bytes_to_gb(virtual_mem.total),
        "available_gb": bytes_to_gb(virtual_mem.available)
    }

def get_disk_info():
    total, used, free = shutil.disk_usage("/")
    return {
        "disk_total_gb": bytes_to_gb(total),
        "disk_free_gb": bytes_to_gb(free)
    }

def get_gpu_info():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"gpu": "NVIDIA GPU not found or `nvidia-smi` not available"}
        lines = result.stdout.strip().splitlines()
        gpus = []
        for line in lines:
            name, mem_total, mem_free = line.split(", ")
            gpus.append({
                "name": name,
                "vram_total_gb": round(int(mem_total) / 1024, 2),
                "vram_free_gb": round(int(mem_free) / 1024, 2)
            })
        return {"gpus": gpus}
    except FileNotFoundError:
        return {"gpu": "nvidia-smi not installed. Possibly no GPU or using AMD/Intel GPU."}

def get_system_summary():
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine()
    }

# === Run Diagnostic ===
if __name__ == "__main__":
    print("\n🖥️ System Summary:")
    print(get_system_summary())

    print("\n🧠 CPU Info:")
    print(get_cpu_info())

    print("\n💾 RAM Info:")
    print(get_ram_info())

    print("\n📀 Disk Info:")
    print(get_disk_info())

    print("\n🎮 GPU Info:")
    print(get_gpu_info())
