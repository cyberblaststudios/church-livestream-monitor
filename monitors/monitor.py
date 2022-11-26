import logging
from monitors.monitor_message import MonitorMessage
from threading import Thread
from queue import Queue
from dateutil import parser
from datetime import datetime, tzinfo
from datetime import timezone
import pytz

class Monitor():

    logger = None
    monitor_thread = None
    monitor_name = str()
    queue = None
    monitor_times = None
    current_timezone = None

    # python dict that will be populated by a section in the json file
    monitor_config = {}

    # member variable to track whether the service monitored is currently down to prevent tons of alerts
    is_down = False

    def __init__(self, logger: logging.Logger, monitor_config: dict, monitor_name: str, queue: Queue) -> None:
        self.logger = logger
        self.monitor_config = monitor_config
        self.monitor_name = monitor_name
        self.queue = queue

        # get the time ranges in the config for this monitor
        self.monitor_times = self.monitor_config.get("monitor_times", None)
        self.current_timezone = pytz.timezone(self.monitor_config.get("timezone", "US/Central"))

        # create and start the monitoring thread
        self.monitor_thread = Thread(target=self.run, daemon=True)
        self.monitor_thread.setName(self.monitor_name)

        self.monitor_thread.start()

    # run function to inherit in child monitor classes
    def run(self) -> None:
        pass

    def should_monitor(self) -> bool:
        return_should_monitor = False

        # if we don't have monitor times configured, we will assume that we want the monitoring to be always on, return True
        if self.monitor_times == None:
            return True

        for time_range in self.monitor_times:
            # get the start time and end time, they should be HH:mm:ss timestamps
            start_time_str = time_range.get("startTime", None)
            end_time_str = time_range.get("endTime", None)

            # check if we got timestamps
            if start_time_str == None or end_time_str == None:
                self.logger.error(f"No timestamps found for {self.monitor_name} from the config file, even though an array is defined")
                continue

            # convert timestamps from HH:mm:ss strings to datetime type
            try:
                start_time = self.current_timezone.localize(parser.parse(start_time_str))
                end_time = self.current_timezone.localize(parser.parse(end_time_str))
            except Exception as e:
                self.logger.error(f"There was an issue with reading the timestamps for {self.monitor_name} from the config file. {e}")
                return False
        
            # get current time and compare with the configured range
            current_time = datetime.now(self.current_timezone)

            if current_time >= start_time and current_time <= end_time:
                return_should_monitor = True

        return return_should_monitor

    def on_service_down(self) -> None:
        if self.is_down == False:
            self.is_down = True

            # alert on the outage
            self.logger.info(f"Thread {self.monitor_name} - experienced outage")

            # put down message into the queue for GUI
            try:
                self.queue.put(MonitorMessage(self.monitor_thread, "stream-down"), False)
            except Exception as e:
                pass
                # we don't care if the queue is full in this case, just pass

    def on_service_up(self) -> None:
        self.is_down = False
