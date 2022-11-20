class MonitorMessage():

    thread_name = ""
    message = ""

    def __init__(self, thread_name: str, message: str) -> None:
        self.thread_name = thread_name
        self.message = message
    