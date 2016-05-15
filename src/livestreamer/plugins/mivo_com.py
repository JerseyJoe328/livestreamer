import re

from livestreamer.plugin import Plugin
from livestreamer.plugin.api import http, validate
from livestreamer.stream import HLSStream

ANONYMOUS_USER_ID = "BY-TrgLgK0NMzXb_JB_81DfeOxK_SNH7"
AUTH_URL = "http://api.mivo.com/v4/web/channels/wms-auth"
CHANNELS_URL = "http://api.mivo.com/v4/web/channels"
VIDEO_URL = "http://api.mivo.com/v4/web/videos/{0}"

_url_re = re.compile("http://www.mivo.com/#/(?:live/(?:(?P<channel>[^/?]+))|(?:video/(?P<video_id>\d+)\+\+))")

_auth_schema = validate.Schema(
    {
        "sign": validate.text
    }
)

_channels_schema = validate.Schema(
    [{
        "dataSlug": validate.text,
        "dataUrl": validate.text
    }]
)

_video_schema = validate.Schema(
    {
        "is_active": bool,
        "url": validate.url(scheme="http")
    }
)

class MivoCom(Plugin):
    @classmethod
    def can_handle_url(cls, url):
        return _url_re.match(url)

    def _get_streams(self):
        match = _url_re.match(self.url)
        if match is None:
            return

        channel = match.group("channel")
        if channel is not None:
            headers = {
                "Authorization": ANONYMOUS_USER_ID
            }
            res = http.get(AUTH_URL, headers=headers)
            auth = http.json(res, schema=_auth_schema)

            res = http.get(CHANNELS_URL)
            channels = http.json(res, schema=_channels_schema)

            for c in channels:
                if c["dataSlug"] == channel:
                    return HLSStream.parse_variant_playlist(self.session, c["dataUrl"] + auth["sign"])

        video_id = match.group("video_id")
        if video_id is not None:
            res = http.get(VIDEO_URL.format(video_id))
            video = http.json(res, schema=_video_schema)
            if video["is_active"]:
                return HLSStream.parse_variant_playlist(self.session, video["url"])

        return

__plugin__ = MivoCom
