from .monitor import Monitor
from facebook_scraper import get_posts
import time

class facebookMonitor(Monitor):

    def run(self) -> None:
        super().run(self)

        page_id = self.monitor_config.get('page_id', None)
        interval = self.monitor_config.get('interval', 60)

        if page_id == None:
            self.logger.error("No page id specified")
            return

        # monitor loop
        while (True):
            is_down = False

            for post in get_posts(page_id, pages=2):
                if post['is_live'] == False:
                    #let the parent class handle the outage
                    self.on_service_down()
            
            # wait for the interval to scrape again
            time.sleep(interval)