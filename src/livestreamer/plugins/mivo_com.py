import re

from livestreamer.plugin import Plugin
from livestreamer.plugin.api import http, validate
from livestreamer.stream import HLSStream

CHANNELS_URL = "http://api.mivo.com/v2/web/channels"

_url_re = re.compile("http://www.mivo.com/#/live/(?P<channel>[^/?]+)")

_schema = validate.Schema(
    [{
        "dataSlug": validate.text,
        "dataUrl": validate.text
    }]
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

        res = http.get(CHANNELS_URL)
        channels = http.json(res, schema=_schema)

        for c in channels:
            if c["dataSlug"] == channel:
                return HLSStream.parse_variant_playlist(self.session, "".join(chr(ord(x)^5) for x in c["dataUrl"]))

        return

__plugin__ = MivoCom
