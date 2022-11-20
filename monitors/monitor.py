import logging
from tarfile import StreamError
from monitors.monitor_message import MonitorMessage
from threading import Thread
from queue import Queue

class Monitor():

    logger = None
    monitor_thread = None
    monitor_name = str()
    queue = None

    # python dict that will be populated by a section in the json file
    monitor_config = {}

    # member variable to track whether the service monitored is currently down to prevent tons of alerts
    is_down = False

    def __init__(self, logger: logging.Logger, monitor_config: dict, monitor_name: str, queue: Queue) -> None:
        self.logger = logger
        self.monitor_config = monitor_config
        self.monitor_name = monitor_name
        self.queue = queue

        # create and start the monitoring thread
        self.monitor_thread = Thread(target=self.run, daemon=True)
        self.monitor_thread.setName(self.monitor_name)

        self.monitor_thread.start()

    # run function to inherit in child monitor classes
    def run(self) -> None:
        pass

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
