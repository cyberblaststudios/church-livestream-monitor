import json
import logging
from logging.handlers import RotatingFileHandler
from queue import Empty, Queue
import signal
import sys
from threading import Thread
from time import sleep
from tkinter import messagebox
import tkinter
from monitors.facebook_monitor import facebookMonitor

LOG_FILE_NAME = "streammonitor.log"

class StreamMonitor:

    config = {}
    applogger = None
    queue = None

    # hold all of the workers, so that we can join on them
    thread_list = []

    def __init__(self, config: dict, applogger: logging.Logger, queue: Queue) -> None:
        self.config = config
        self.applogger = applogger
        self.queue = queue

    def start_workers(self) -> None:
        monitor_config = self.config.get('monitors', None)

        if monitor_config == None:
            self.applogger.error("invalid monitor config")
            return

        # create all of the workers based on config file
        for monitor_name in monitor_config.keys():
            monitor = monitor_config.get(monitor_name)
            
            if monitor.get('type') == "facebook":
                # start up a facebook worker
                facebook_worker_inst = facebookMonitor(self.applogger, monitor, monitor_name, self.queue)
                self.thread_list.append(facebook_worker_inst.monitor_thread)
        
        while True:
            message = None
            try:
                message = self.queue.get_nowait()
            except Empty as e:
                pass
            
            # handle message
            if message != None and message.message == "stream-down":
                # calling withdraw to prevent a blank tk dialog box from showing
                tkinter.Tk().withdraw()

                # dialoge box as a warning that the stream is down
                messagebox.showwarning(f"{message.thread_name} is down")

    def start(self):
        monitor_manager_thread = Thread(target=self.start_workers, name="monitor_manager_thread", daemon=True)
        monitor_manager_thread.start()

        try:
            while monitor_manager_thread.is_alive:
                sleep(.1)
        except KeyboardInterrupt:
            print("stopping monitor....")

def main():

    # holds configuration values
    config = {}

    # create the thread message queue
    message_queue = Queue(100)

    # setup basic logging parameters
    logging.basicConfig(filename=LOG_FILE_NAME, 
        format="%(asctime)s %(levelname)s %(threadName)s %(message)s", level="DEBUG", filemode="a")

    #main program logger
    applogger = logging.getLogger()

    # configure log rotations
    applogger.addHandler(RotatingFileHandler(filename=LOG_FILE_NAME, maxBytes=100000000, backupCount=4))

    # also emit logs to stdout
    applogger.addHandler(logging.StreamHandler(sys.stdout))

    # load configuration
    with open("config.json", "r") as open_file:
        try:
            config = json.loads(open_file.read())
        except BaseException as exception:
            applogger.fatal(f"Failed to open configuration file: {exception}")
            sys.exit(1)

    # apply the log level from configuration file
    applogger.setLevel(config.get('log_level', None))

    # create an instance of the StreamMonitor, then start up the monitor workers
    stream_montitor_app = StreamMonitor(config, applogger, message_queue)

    # build the monitor workers - blocking call
    stream_montitor_app.start()
    

if __name__ == "__main__":
    main()