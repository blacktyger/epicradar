import json
import threading
from subprocess import Popen, PIPE
import psutil
import time
from datetime import datetime

now = datetime.now().strftime('%H:%M:%S')


class Program:
    def __init__(self, name, process_name, path):
        self.name = name
        self.process_name = process_name
        self.path = path
        self.cmd_name = process_name

    def __str__(self):
        return f"{self.name}"


class Command(threading.Thread):
    def __init__(self, command, password, node):
        super().__init__()

        self.command = command
        self.password = password
        self.node = node
        self.full_cmd = f'epic-wallet -p {self.password} -r {self.node} {command}'.split(" ")
        self.process = Popen(self.full_cmd, stdout=PIPE, stderr=PIPE,
                             universal_newlines=True, bufsize=1)
        self.stdout, self.stderr = self.process.communicate()


class OwnerApi(Command):
    def __init__(self, target, name, password, command="owner-api", node='local_node'):
        super().__init__(command, password)
        self.name = name
        self.command = command
        self.password = password
        self.target = target

    def run(self):
        owner_thread = Command(command="owner_api", password=self.password)
        owner_thread.start()
        target_thread = threading.Thread(name='target_thread', target=self.target)
        target_thread.start()
        time.sleep(3)
        self.kill_listener()

    @staticmethod
    def kill_listener(self):
        x = check_process(name='epic-wallet')
        try:
            if x:
                print(f"KILLED: {x}")
                x.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
            print("trying to kill owner listener")


def check_process(name):
    # Iterate over the all the running process
    for process in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if name.lower() in process.name().lower():
                return process
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def get_process_id(name):
    process_list = []
    # Iterate over the all the running process
    for process in psutil.process_iter():
        try:
            pinfo = process.as_dict(attrs=['pid', 'name', 'create_time'])
            # Check if process name contains the given name string.
            if name.lower() in pinfo['name'].lower():
                process_list.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return process_list


def kill_process(process):
    try:
        process.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as er:
        print(er)
        pass
    return print(f"[{now}]: (PID:{process.ppid()}) {process.name()} is closed")


def process_manager(name, kill=False, get_list=False):
    # Check if process :name was running or not.
    try:
        if check_process(name):
            # Find details of all the running instances of process that contains :name
            process_list = [proc for proc in psutil.process_iter() if name in proc.name().lower()]
            if len(process_list) > 0:
                for process in process_list:
                    # print(f"[{now}]: {str(process).split('(')[1][:-1]}")
                    if kill:
                        kill_process(process)
                        print(f"{process} killed")
            else:
                return False

            if get_list:
                return process_list
        else:
            print(f'No {name} process was running')
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as err:
        print(err)
        pass
