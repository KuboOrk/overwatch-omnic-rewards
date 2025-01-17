import json
import logging
import random
import time

# Dependencies
import requests

logger = logging.getLogger(__name__)


class Viewer:

    TRACKING_OWL = "https://pk0yccosw3.execute-api.us-east-2.amazonaws.com/production/v2/sentinel-tracking/owl"
    TRACKING_OWC = "https://pk0yccosw3.execute-api.us-east-2.amazonaws.com/production/v2/sentinel-tracking/contenders"

    CONNECT_TIMEOUT = 5
    READ_TIMEOUT = 10

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.6; rv:102.0) Gecko/20100101 Firefox/102.0',
        'Mozilla/5.0 (X11; Linux i686; rv:102.0) Gecko/20100101 Firefox/102.0',
        'Mozilla/5.0 (Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:102.0) Gecko/20100101 Firefox/102.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
        'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/100.0'
    ]

    def __init__(self, account_id, video_id, event_id, contenders=False):
        self.session = requests.Session()
        self.__set_headers()
        self.time_watched = 0
        self.account_id = account_id
        self.video_id = video_id
        self.event_id = event_id
        self.contenders = contenders
        self.url = self.TRACKING_OWC if contenders else self.TRACKING_OWL

    def __set_headers(self):
        user_agent = random.choice(self.USER_AGENTS)
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept-Language': 'en-GB,en;q=0.5',
            'Referer': 'https://overwatchleague.com/',
            'Origin': 'https://overwatchleague.com',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'Trailers',
        })

    def fake_view_loop(self):
        while self.send_sentinel_packets():
            time.sleep(60)
            self.time_watched += 1
        return self.time_watched

    def send_sentinel_packets(self):
        # Send OPTIONS
        r1 = self.__send_options_packet()
        r1.raise_for_status()

        # Send POST
        r2 = self.__send_post_packet()
        r2.raise_for_status()

        logger.debug(f"POST Response - {r2.text}")

        # Parse Response
        resd = json.loads(r2.text)
        if resd["status"] != 200:
            raise ViewerStatusCodeError(r2.text)
        if resd["data"]["continueTracking"]:
            return True
        return False

    def restart_session(self):
        self.session = requests.Session()
        self.__set_headers()

    def __send_options_packet(self):
        headers = {
            'Accept': '*/*',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type,x-origin'
        }

        response = self.session.options(self.url, headers=headers, timeout=(self.CONNECT_TIMEOUT, self.READ_TIMEOUT))
        return response

    def __send_post_packet(self):
        headers = {
            'Accept': 'application/json',
            'x-origin': 'overwatchleague.com',
            'Content-Type': 'application/json',
        }

        data = {
            "accountId": str(self.account_id),
            "videoId": self.video_id,
            "type": "video_player",
            "entryId": self.event_id,
            "liveTest": False,
            "locale": "en-us",
            "timestamp": int(time.time()),
            "contentType": "live",
            "id_type": "battleNetId"
        }
        logger.debug(data)
        response = self.session.post(self.url, headers=headers, data=json.dumps(data),
                                     timeout=(self.CONNECT_TIMEOUT, self.READ_TIMEOUT))
        return response


class ViewerStatusCodeError(Exception):

    def __init__(self, response):
        super().__init__(self)
        self.response = response

    def __str__(self):
        return f"Bad Response: {self.response}"


def main():
    account_id = ""
    video_id = ""
    owc_event_id = "blt942744e48c33cdc9"
    watcher = Viewer(account_id, video_id, owc_event_id)
    r = watcher.send_sentinel_packets()
    print(r)

    owl_event_id = "bltfed4276975b6d58a"
    watcher = Viewer(account_id, video_id, owl_event_id)
    r = watcher.send_sentinel_packets()
    print(r)


if __name__ == "__main__":
    main()
