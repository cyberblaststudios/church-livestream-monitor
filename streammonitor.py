from asyncio.log import logger
import csv
from fileinput import filename
import json
import logging
from logging import exception
from monitors.facebook_monitor import facebookMonitor


def start_workers(config: dict, applogger: logger) -> None:
    monitor_config = config.get('monitors', None)

    if monitor_config == None:
        applogger.error("invalid monitor config")
        return
    
    # create all of the workers based on config file
    for monitor_name in monitor_config.keys():
        monitor = monitor_config.get(monitor_name)
        
        if monitor.get('type') == "facebook":
            # start up a facebook worker
            facebook_worker_inst = facebookMonitor(logger, monitor)


def main():

    # holds configuration values
    config = {}

    # setup logging
    logging.basicConfig(filename="streammonitor.log", 
        format="%(asctime)s %(levelname)s %(threadName)s %(message)s", level="DEBUG", filemode="w")

    #main program logger
    applogger = logging.getLogger()

    # load configuration
    with open("config.json", "r") as open_file:
        try:
            config = json.loads(open_file)
        except exception:
            applogger.fatal(f"Failed to open configuration file: {exception}")
            exit(1)

    # apply the log level from configuration file
    applogger.setLevel(config.get('log_level', None))

    # build the monitor workers
    start_workers(config, applogger)
    

if __name__ == "__main__":
    main()