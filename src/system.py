import platform
import socket

def get_system_info():
    """Return basic information about the current system"""
    return {
        "hostname":socket.gethostname(),
        "operating_system":platform.system(),
        "os_release":platform.release(),
        "architecture":platform.machine(),
        "python_version":platform.python_version()
    }
if __name__=="__main__":
    get_system_info()