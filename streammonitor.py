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
import os

LOG_FILE_NAME = 'logs/streammonitor.log'

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
            try:
                # give us enough sleep time to catch SIGKILL
                sleep(.1)

                message = None
                try:
                    message = self.queue.get_nowait()
                except Empty as e:
                    # handle queue exceptions
                    pass

                # handle message
                if message != None and message.message == "stream-down":
                    # calling withdraw to prevent a blank tk dialog box from showing
                    tkinter.Tk().withdraw()

                    # dialoge box as a warning that the stream is down
                    messagebox.showwarning(f"{message.thread_name} is down")

            except KeyboardInterrupt:
                        print("stopping monitor....")
                        return

def main():

    # holds configuration values
    config = {}

    # create the thread message queue
    message_queue = Queue(100)

    # get the parent directories that need to be created from LOG_FILE_NAME
    split_logging_path = os.path.split(LOG_FILE_NAME)

    # make sure that the logs directory is created
    if split_logging_path != None and split_logging_path[0] != '':
        try:
            # create the directories that the log file needs to be in before we create the log file
            os.makedirs(split_logging_path[0], exist_ok=True)
        except Exception as e:
            print("failed to create log file directory, perhaps the process does not have permission")
            sys.exit(1)

    # setup basic logging parameters
    logging.basicConfig(filename=LOG_FILE_NAME, 
        format="%(asctime)s %(levelname)s %(threadName)s %(message)s", level="DEBUG", filemode="a")

    #main program logger
    applogger = logging.getLogger()

    # configure log rotations
    applogger.addHandler(RotatingFileHandler(filename=LOG_FILE_NAME, maxBytes=20000000, backupCount=4))

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
    stream_montitor_app.start_workers()
    

if __name__ == "__main__":
    main()