from asyncio.log import logger
from msilib.schema import ControlCondition
from typing import Dict
from .monitor import Monitor
from facebook_scraper import get_posts
import time
from datetime import datetime
from datetime import timezone

class facebookMonitor(Monitor):

    def get_latest_post(self, page_id, timezone) -> Dict:

        latest_post = None

        posts = get_posts(page_id, pages=4)

        for post in posts:
            current_time = datetime.now(self.current_timezone)
            post_time_str = post.get('time', None)

            if post_time_str == None:
                continue

            # localize the date object so that we can perform comparisons with both objects being offset-aware datetime objects
            post_time = self.current_timezone.localize(post_time_str)
            
            # if there is no latest post yet, make this one the latest if it's not in the future
            if latest_post == None and post_time <= current_time:
                latest_post = post
                continue
            
            if latest_post != None:
                latest_post_time = self.current_timezone.localize(latest_post.get('time', None))

            # check if this post is newer than the current latest one and make sure that it is not in the future
            if latest_post != None and post_time <= current_time and post_time > latest_post_time:
                latest_post = post
        
        return latest_post

    def run(self) -> None:
        super().run()

        page_id = self.monitor_config.get('page_id', None)
        interval = self.monitor_config.get('interval', 60)

        if page_id == None:
            self.logger.error("No page id specified")
            return

        # monitor loop
        while (True):

            # only monitor during the configured time
            if not self.should_monitor():
                self.logger.debug(f"not in the time range for monitoring, waiting to monitor until current time is in the configured time range")
                time.sleep(interval)
                continue
            
            # make sure that we are getting the latest post from the configured Facebook page
            latest_post = self.get_latest_post(page_id, self.current_timezone)                

            # retrieve the live status from the scraped page data
            live_status = latest_post.get('is_live', None)

            if live_status == None:
                self.logger.info(f"post did not have live status to pull from Facebook page {page_id}")
                time.sleep(interval)
                continue

            if not live_status:
                # let the parent class handle the outage
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