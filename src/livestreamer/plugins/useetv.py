import re

from livestreamer.plugin import Plugin
from livestreamer.plugin.api import http, validate
from livestreamer.stream import HLSStream, RTMPStream

CLIENT_IP_URL = "http://my.useetv.com/ip_client.php"
STREAM_AUTH_URL = "http://www.useetv.com/services/tv_play_auth"
VIDEO_AUTH_URL = "http://www.useetv.com/services/movie_play_auth"

_url_re = re.compile(r"http://www.useetv.com/(?:(?:livetv/(?P<channel_id>\w+))|(?:play/\w+/(?P<video_id>\d+)/))")
_client_ip_re = re.compile(r"var  real_ip_client = '(?P<client_ip>[^']+)';")

_auth_schema = validate.Schema({
    "resultCode": int,
    "resultMessage": validate.text,
    validate.optional("stream_url"): validate.url(scheme=validate.any("rtmp", "http"))
})

class UseeTV(Plugin):
    @classmethod
    def can_handle_url(cls, url):
        return _url_re.match(url)

    def _get_client_ip(self):
        res = http.get(CLIENT_IP_URL)
        match = _client_ip_re.match(res.text)
        if match is None:
            return None
        else:
            return match.group("client_ip")
        print(res.text)

    def _get_streams(self):
        match = _url_re.match(self.url)
        if match is None:
            return

        channel_id = match.group("channel_id")
        if channel_id:
            client_ip = self._get_client_ip()
            if client_ip is None:
                return

            params = {
                "channel_code": channel_id,
                "ip": client_ip,
                "vd_service": "livetv",
                "token": "",
                "starttime": "",
                "endtime": ""
            }

            res = http.post(STREAM_AUTH_URL, params=params)
            auth_info = http.json(res, schema=_auth_schema)
            if auth_info["resultCode"] == 0:
                if "stream_url" in auth_info:
                    return HLSStream.parse_variant_playlist(self.session, auth_info["stream_url"])
            elif auth_info["resultCode"] == 303:
                self.logger.warning("Stream is geo-restricted")

        return

__plugin__ = UseeTV
