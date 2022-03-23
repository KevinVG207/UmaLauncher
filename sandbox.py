import psutil

for proc in psutil.process_iter():
    try:
        if "nordvpn.exe" in proc.name().lower():
            print(proc.name())
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass