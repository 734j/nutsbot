import argparse
import getpass
import sys
import os
import subprocess

def install_service(root_run_dir_path: str, user: str) -> bool:

    print(f"Elevated privelege to user: {getpass.getuser()}")
    print("Installing the service.")
    ExecStart = f"{sys.executable} bot.py"
    WorkingDirectory = root_run_dir_path
    if not os.path.isfile("nutsbot.service"):
        print("nutsbot.service does not exist.")
        return False
    
    FILEservice = open("nutsbot.service", "r")
    data = FILEservice.read()
    FILEservice.close()
    data = data.replace("__USER__", user)
    data = data.replace("__EXEC_START__", ExecStart)
    data = data.replace("__ROOT_RUN_DIR__", WorkingDirectory)
    FILEservice = open("nutsbot.service.tmp", "w")
    FILEservice.write(data)
    FILEservice.close()
    os.rename("nutsbot.service.tmp", "/etc/systemd/system/nutsbot.service")
    print("nutsbot.service.tmp -> /etc/systemd/system/nutsbot.service")
    return True

def enable_service():
    print("Enabling the service...")
    subprocess.run(["sudo", "systemctl", "enable", "nutsbot.service"], check=True)
    
def stop_service():

    print("Stopping the service...")
    subprocess.run(["sudo", "systemctl", "stop", "nutsbot.service"], check=True)
    
def start_service():

    print("Starting the service...")
    subprocess.run(["sudo", "systemctl", "start", "nutsbot.service"], check=True)

    
parser = argparse.ArgumentParser(description="nutsbot Service helper (for elevated priveleges)")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--start', action='store_true', help='Start the service')
group.add_argument('--stop', action='store_true', help='Stop the service')
group.add_argument('--enable', action='store_true', help='Enable the service')
group.add_argument('--install', nargs=2, metavar=('ARG1', 'ARG2'), help='Install the service')

args = parser.parse_args()

if args.start:
    start_service()
elif args.stop:
    stop_service()
elif args.enable:
    enable_service()
elif args.install:
    arg1, arg2 = args.install
    install_service(arg1, arg2)
