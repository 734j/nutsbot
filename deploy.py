#!/usr/bin/python3

import subprocess
import argparse
import json
import os
from datetime import datetime
import shutil
import sys
import getpass

g_run_dir_path = "run_dir_path"
g_token_file_path = "token_file_path"
g_bot_src = "bot.py"
g_bot_src_test = "bot_test.py"
g_run_dir_path_test = "./test"
g_user = getpass.getuser()

def ask_yes_no(question: str) -> bool:
    while True:
        answer = input(f"{question} [Y/N]: ").strip().lower()
        if answer in ['y', 'yes']:
            return True
        elif answer in ['n', 'no']:
            return False
        else:
            print("Please enter Y or N.")

def install_systemd_service(root_run_dir_path: str, user: str):
    subprocess.run(["sudo", "python3", "systemd-service-utility.py", "--install", root_run_dir_path, user], check=True)

def stop_systemd_service():
    subprocess.run(["sudo", "python3", "systemd-service-utility.py", "--stop"], check=True)

def start_systemd_service():
    subprocess.run(["sudo", "python3", "systemd-service-utility.py", "--start"], check=True)

def enable_systemd_service():
    subprocess.run(["sudo", "python3", "systemd-service-utility.py", "--enable"], check=True)
    
def get_current_commit_hash():
    try:
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], 
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')
        return commit_hash
    except subprocess.CalledProcessError:
        return None

def is_config_valid(config_file: str) -> bool:
    
    FILE = open(config_file,"r")
    config_json = FILE.read()
    config = json.loads(config_json)
    allowed = {g_token_file_path, g_run_dir_path}
    if set(config) <= allowed:
        return True
    
    return False

def install_bot(conf_path: str):

    print("Installing...")
    if not is_config_valid(conf_path):
        print("Invalid config")
        return

    print("OK config.")
    FILEjson = open(conf_path, "r")
    config_json = FILEjson.read()
    config = json.loads(config_json)
    FILEtoken = open(config[g_token_file_path])
    root_run_dir_path = os.path.expanduser(config[g_run_dir_path]) # Path to root of the run dir
    token_string = FILEtoken.read() # String of token
    token_string = token_string.strip('\n')
    
    directory_paths = [
        os.path.expanduser(root_run_dir_path+"/database"),
        os.path.expanduser(root_run_dir_path+"/old-versions")
    ]

    for path in directory_paths:
        try:
            os.makedirs(path, exist_ok=True)
            print(f"OK: {path}")
        except PermissionError:
            print(f"Insufficient Permission to create: {path}")
        except OSError as e:
            print(f"Error creating path: {path}: {e}")


    fd2 = os.open(root_run_dir_path+"/bot.py", os.O_WRONLY | os.O_CREAT)
    os.close(fd2)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    os.rename(root_run_dir_path+"/"+g_bot_src, directory_paths[1]+"/bot"+timestamp+".py")
    shutil.copyfile(g_bot_src, root_run_dir_path+"/"+g_bot_src)

    FILEinstalled = open(root_run_dir_path+"/"+g_bot_src, "r")
    data = FILEinstalled.read()
    FILEinstalled.close()
    data = data.replace("__YOUR_TOKEN__", token_string)
    data = data.replace("__YOUR_DATABASE_PATH__", directory_paths[0])
    data = data.replace("__VERSION__", get_current_commit_hash())
    FILEinstalled = open(root_run_dir_path+"/"+g_bot_src, "w")
    FILEinstalled.write(data)
    FILEinstalled.close()
    if ask_yes_no("Do you want to install the bot as a SystemD service?") is True:
        install_systemd_service(root_run_dir_path, g_user)
        if ask_yes_no("Would you like to enable and start the service?") is True:
            enable_systemd_service()
            start_systemd_service()
                
        elif False:
            print("There was an issue installing the SystemD service.")
    elif False:
        print("SystemD service not installed.")
        
    
def test_bot(conf_path: str):

    print("Deploying testfile...")
    if not is_config_valid(conf_path):
        print("Invalid config")
        return

    print("OK config.")
    FILEjson = open(conf_path, "r")
    config_json = FILEjson.read()
    config = json.loads(config_json)
    FILEtoken = open(config[g_token_file_path])
    root_run_dir_path_test = os.path.expanduser(g_run_dir_path_test) # Path to root of the run dir
    root_run_dir_path = os.path.expanduser(config[g_run_dir_path])
    token_string = FILEtoken.read() # String of token
    token_string = token_string.strip('\n')
    
    directory_paths = [
        os.path.expanduser(root_run_dir_path+"/database"),
        os.path.expanduser(root_run_dir_path+"/old-versions")
    ]

    for path in directory_paths:
        if not os.path.isdir(path):            
            print(f"Directory {path} does not exist. Please use --install.")
            return False
    
    shutil.copyfile(g_bot_src, root_run_dir_path_test+"/"+g_bot_src_test)

    FILEinstalled = open(root_run_dir_path_test+"/"+g_bot_src_test, "r")
    data = FILEinstalled.read()
    FILEinstalled.close()
    data = data.replace("__YOUR_TOKEN__", token_string)
    data = data.replace("__YOUR_DATABASE_PATH__", directory_paths[0])
    data = data.replace("__VERSION__", get_current_commit_hash())
    FILEinstalled = open(root_run_dir_path_test+"/"+g_bot_src_test, "w")
    FILEinstalled.write(data)
    FILEinstalled.close()
    print(f"Updated to commit: {get_current_commit_hash()}\nBot moved to ./test for testing.")
    if ask_yes_no("Would you like to stop the service to test now?") is True:
        stop_systemd_service()

def update_bot(conf_path: str):

    print("Deploying update...")
    if not is_config_valid(conf_path):
        print("Invalid config")
        return

    print("OK config.")
    FILEjson = open(conf_path, "r")
    config_json = FILEjson.read()
    config = json.loads(config_json)
    FILEtoken = open(config[g_token_file_path])
    root_run_dir_path = os.path.expanduser(config[g_run_dir_path])
    token_string = FILEtoken.read() # String of token
    token_string = token_string.strip('\n')
    
    directory_paths = [
        os.path.expanduser(root_run_dir_path+"/database"),
        os.path.expanduser(root_run_dir_path+"/old-versions")
    ]

    for path in directory_paths:
        if not os.path.isdir(path):            
            print(f"Directory {path} does not exist. Please use --install.")
            return False

    if not os.path.isfile(root_run_dir_path+"/bot.py"):
        print(f"bot.py does not exist, this is not an update operation. Please use --install.")
        return False

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    os.rename(root_run_dir_path+"/"+g_bot_src, directory_paths[1]+"/bot"+timestamp+".py")
    shutil.copyfile(g_bot_src, root_run_dir_path+"/"+g_bot_src)
    
    FILEinstalled = open(root_run_dir_path+"/"+g_bot_src, "r")
    data = FILEinstalled.read()
    FILEinstalled.close()
    data = data.replace("__YOUR_TOKEN__", token_string)
    data = data.replace("__YOUR_DATABASE_PATH__", directory_paths[0])
    data = data.replace("__VERSION__", get_current_commit_hash())
    
    FILEinstalled = open(root_run_dir_path+"/"+g_bot_src, "w")
    FILEinstalled.write(data)
    FILEinstalled.close()
    print(f"Updated to commit: {get_current_commit_hash()}\nBot has been updated successfully.")
    if ask_yes_no("Would you like to restart the service?") is True:
        stop_systemd_service()
        start_systemd_service()
    

parser = argparse.ArgumentParser(description="Bot tool")
parser.add_argument("config_file", type=str, nargs='?', help="Path to the config file (required for most operations)")

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--test', action='store_true', help="Run tests")
group.add_argument('--install', action='store_true', help="Run installation")
group.add_argument('--update', action='store_true', help="Run update")
group.add_argument('--usage', action='store_true', help="A more in depth explanation of the options.")
group.add_argument('--stopservice', action='store_true', help="Stop service")
group.add_argument('--startservice', action='store_true', help="Start service")

args = parser.parse_args()

if args.stopservice:
    stop_systemd_service()
    sys.exit(0)
if args.startservice:
    start_systemd_service()
    sys.exit(0)

if args.usage:
    print(f"{sys.argv[0]}\n")
    print("     --test        Will install the bot in to a separate testing runtime directory. For your testing purposes.")
    print("     --install     Will install the bot for the first time on your system in the way it's intended to run. Assumes you are on linux with SystemD.")
    print("     --update      Will update already installed bot. Works almost just like --install, just that it wont ask to install the service.")
    print("     --usage       Display this message.\n")
    sys.exit(0)

if not args.config_file:
    parser.error("A config file is required. Please check example-config.json for an example.")

conf_path = args.config_file

if args.test:
    test_bot(conf_path)
elif args.install:
    install_bot(conf_path)
elif args.update:
    update_bot(conf_path)
