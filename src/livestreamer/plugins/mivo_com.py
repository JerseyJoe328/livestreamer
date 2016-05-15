import re

from livestreamer.plugin import Plugin, PluginOptions
from livestreamer.plugin.api import http, validate
from livestreamer.stream import HLSStream

ANONYMOUS_USER_ID = "BY-TrgLgK0NMzXb_JB_81DfeOxK_SNH7"
LOGIN_URL = "http://api.mivo.com/v4/web//users/signin"
AUTH_URL = "http://api.mivo.com/v4/web/channels/wms-auth"
CHANNELS_URL = "http://api.mivo.com/v4/web/channels"
VIDEO_URL = "http://api.mivo.com/v4/web/videos/{0}"

_url_re = re.compile("http://www.mivo.com/#/(?:live/(?:(?P<channel>[^/?]+))|(?:video/(?P<video_id>\d+)\+\+))")

_login_schema = validate.Schema(
    {
        "token": validate.text
    },
    validate.get("token")
)

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
    options = PluginOptions({
        "email": None,
        "password": None
    })

    @classmethod
    def can_handle_url(cls, url):
        return _url_re.match(url)

    def _authenticate(self, email, password):
        token = ANONYMOUS_USER_ID

        if email and password:
            data = {
                "email": email,
                "password": password
            }

            res = http.post(LOGIN_URL, data=data, acceptable_status=(201, 401))
            if res.status_code == 201:
                token = http.json(res, schema=_login_schema)

        return token

    def _get_streams(self):
        match = _url_re.match(self.url)
        if match is None:
            return

        token = self._authenticate(self.options.get("email"), self.options.get("password"))

        channel = match.group("channel")
        if channel is not None:
            headers = {
                "Authorization": token
            }
            res = http.get(AUTH_URL, headers=headers, acceptable_status=(200, 403))
            if res.status_code == 200:
                auth = http.json(res, schema=_auth_schema)
                sign = auth["sign"]
            else:
                sign = "?video"

            res = http.get(CHANNELS_URL)
            channels = http.json(res, schema=_channels_schema)

            for c in channels:
                if c["dataSlug"] == channel:
                    return HLSStream.parse_variant_playlist(self.session, c["dataUrl"] + sign)

        video_id = match.group("video_id")
        if video_id is not None:
            res = http.get(VIDEO_URL.format(video_id))
            video = http.json(res, schema=_video_schema)
            if video["is_active"]:
                return HLSStream.parse_variant_playlist(self.session, video["url"])

        return

__plugin__ = MivoCom
