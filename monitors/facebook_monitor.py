from asyncio.log import logger
from .monitor import Monitor
from facebook_scraper import get_posts
import time

class facebookMonitor(Monitor):

    def run(self) -> None:
        super().run()

        page_id = self.monitor_config.get('page_id', None)
        interval = self.monitor_config.get('interval', 60)

        if page_id == None:
            self.logger.error("No page id specified")
            return

        # monitor loop
        while (True):

            for post in get_posts(page_id, pages=4):
                page_id = self.monitor_config.get('page_id', "<Page ID not found in config dict>")                    

                if post['is_live'] == False:
                    #let the parent class handle the outage
                    self.on_service_down()

                else:
                    if self.is_down == True:
                        # reset the outage flag
                        self.on_service_up()
                        self.logger.info(f"stream started or is back up - service is live on Facebook page {page_id}")

                    # log a message for the facebook feed being successful
                    self.logger.info(f"stream update is successful - service is live on Facebook page {page_id}")
            
            # wait for the interval to scrape again
            time.sleep(interval)