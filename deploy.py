#!/usr/bin/python3

import subprocess
import argparse
import json
import os
from datetime import datetime
import shutil
import sys
import getpass
import sqlite3
import logging


g_bot_src = "bot.py"
g_bot_src_test = "bot_test.py"
g_run_dir_path_test = "./test"
g_user = getpass.getuser()

G_DEBUG = True

def print_debug(text: str):
    if G_DEBUG == False:
        return
    else:
        print(text)

def is_db_empty(db_connection: sqlite3.Connection) -> bool:
    db_cursor = db_connection.cursor()
    db_cursor.execute("""
    SELECT COUNT(*) 
    FROM sqlite_master 
    WHERE type = 'table' AND name NOT LIKE 'sqlite_%';
    """)

    count = db_cursor.fetchone()[0]
    print_debug(count)
    if count == 0:
        return True
    else:
        return False


def initialize_db_tables(db_connection: sqlite3.Connection):
    db_cursor = db_connection.cursor()
    db_cursor.execute("PRAGMA foreign_keys = ON;")
    db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS guilds (
        guild_id TEXT PRIMARY KEY,
        guild_name TEXT NOT NULL,
        guild_size INTEGER DEFAULT 0,
        bot_is_enabled BOOLEAN DEFAULT 1,
        max_triggers INTEGER DEFAULT 50 CHECK (max_triggers BETWEEN 1 AND 50),
        owner_id TEXT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Reactions / Triggers Table
    db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS reactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT NOT NULL,
        trigger_phrase TEXT NOT NULL,
        response_phrase TEXT NOT NULL,
        FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
        UNIQUE(guild_id, trigger_phrase)
    );
    """)

    db_cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS add_default_reaction_on_guild_insert
    AFTER INSERT ON guilds
    BEGIN
        INSERT OR IGNORE INTO reactions (guild_id, trigger_phrase, response_phrase)
        VALUES (NEW.guild_id, 'nuts', '<:nuts:1424932626023841893>');
    END;
    """)

    db_cursor.execute("""
    CREATE TABLE ignored_channels (
    channel_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, channel_id),
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
    );
    """)
    
    db_connection.commit()
    print_debug("initialize_db_tables: Database initialized.")
    
    
def create_db_sqlite3(path: str) -> bool:
    db_connection = sqlite3.connect(path);
    if is_db_empty(db_connection) == True:
        initialize_db_tables(db_connection)
        db_connection.close()
        print_debug("create_db_sqlite3: Database initialized.")
        return True
    else:
        db_connection.close()
        print_debug("create_db_sqlite3: Nothing done. Database already exists.")
        return False
    

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


g_run_dir_path = "run_dir_path"
g_token_file_path = "token_file_path"
g_sqlite3_db_path = "sqlite3_db_path"
g_sqlite3_no_db_path = "sqlite3_no_db_path"
def is_config_valid(config_file: str) -> bool:
    
    FILE = open(config_file,"r")
    config_json = FILE.read()
    config = json.loads(config_json)
    allowed = {g_token_file_path, g_run_dir_path, g_sqlite3_db_path, g_sqlite3_no_db_path}
    if set(config) <= allowed:
        return True
    
    return False

def read_and_format_config(conf_path: str) -> dict[str, str]:
    FILEjson = open(conf_path, "r")
    config_content = FILEjson.read()
    config_json_obj = json.loads(config_content)

    data = {}
    #Step 1: Get the token
    FILEtoken = open(config_json_obj[g_token_file_path])
    data["token_str"] = FILEtoken.read()
    data["token_str"] = data["token_str"].strip('\n')
    
    #Step 2: Determine running directory AKA bot root
    data["root_run_dir_path"] = os.path.expanduser(config_json_obj[g_run_dir_path])

    #Step 3: Sqlite database path
    data["sqlite3_db_path"] = os.path.expanduser(config_json_obj[g_sqlite3_db_path])

    #Step 4: true or false
    data["sqlite3_no_db_path"] = os.path.expanduser(config_json_obj[g_sqlite3_no_db_path])

    return data
    
def install_bot(conf_path: str):

    print("Installing...")
    print("Validating config structure.")
    if not is_config_valid(conf_path):
        print("Invalid config")
        return

    print("OK config.")

    config_data = read_and_format_config(conf_path)

    token_string = config_data.get("token_str")
    root_run_dir_path = config_data.get("root_run_dir_path")
    sqlite3_db_path = config_data.get("sqlite3_db_path")
    sqlite3_no_db_path = config_data.get("sqlite3_no_db_path")

    
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


    if sqlite3_no_db_path == "false":
        create_db_sqlite3(sqlite3_db_path)
    else:
        create_db_sqlite3(directory_paths[0]+"/"+"database.db")

    
    fd2 = os.open(root_run_dir_path+"/bot.py", os.O_WRONLY | os.O_CREAT)
    os.close(fd2)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    os.rename(root_run_dir_path+"/"+g_bot_src, directory_paths[1]+"/bot"+timestamp+".py")
    shutil.copyfile(g_bot_src, root_run_dir_path+"/"+g_bot_src)

    FILEinstalled = open(root_run_dir_path+"/"+g_bot_src, "r")
    data = FILEinstalled.read()
    FILEinstalled.close()
    data = data.replace("__YOUR_TOKEN__", token_string)

    if sqlite3_no_db_path == "false":
        data = data.replace("__YOUR_DATABASE_PATH__", sqlite3_db_path)
    else:
        data = data.replace("__YOUR_DATABASE_PATH__", directory_paths[0]+"/"+"database.db")

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
            

def update_bot(conf_path: str):

    print("Deploying update...")
    print("Validating config structure.")
    if not is_config_valid(conf_path):
        print("Invalid config")
        return

    print("OK config.")

    config_data = read_and_format_config(conf_path)
    token_string = config_data.get("token_str")
    root_run_dir_path = config_data.get("root_run_dir_path")
    sqlite3_db_path = config_data.get("sqlite3_db_path")
    sqlite3_no_db_path = config_data.get("sqlite3_no_db_path")
    
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
    
    if sqlite3_no_db_path == "false":
        data = data.replace("__YOUR_DATABASE_PATH__", sqlite3_db_path)
    else:
        data = data.replace("__YOUR_DATABASE_PATH__", directory_paths[0]+"/"+"database.db")


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
    print("     --install     Will install the bot for the first time on your system in the way it's intended to run. Assumes you are on linux with SystemD.")
    print("     --update      Will update already installed bot. Works almost just like --install, just that it wont ask to install the service.")
    print("     --usage       Display this message.\n")
    sys.exit(0)

if not args.config_file:
    parser.error("A config file is required. Please check example-config.json for an example.")

conf_path = args.config_file


if args.install:
    install_bot(conf_path)
elif args.update:
    update_bot(conf_path)
