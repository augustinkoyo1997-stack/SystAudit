print("SystemAudit - system information Tool")
#version  synchronised whith Github

from system import get_system_info
def main():
   system_info=get_system_info()
   print("==SysAudit - System Information ==")
   for key,value in system_info.items():
     print(f"{key}: {value}")
if __name__=="__main__":
   main()