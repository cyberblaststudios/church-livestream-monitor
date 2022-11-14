import logging

class Monitor():

    logger = None

    # python dict that will be populated by a section in the json file
    monitor_config = {}

    # member variable to track whether the service monitored is currently down to prevent tons of alerts
    is_down = False

    def __init__(self, logger: logging.Logger, monitor_config: dict) -> None:
        self.logger = logger
        self.monitor_config = monitor_config
    
    # run function to inherit in child monitor classes
    def run(self) -> None:
        pass

    def on_service_down(self) -> None:
        if self.is_down == False:
            self.is_down = True

            # alert on the outage
    def on_service_up(self) -> None:
        self.is_down = False
