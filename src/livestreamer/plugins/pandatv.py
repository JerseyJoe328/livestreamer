"""Plugin for panda.tv by Fat Deer"""

import re
import types
from livestreamer.plugin import Plugin
from livestreamer.plugin.api import http, validate
from livestreamer.plugin.api.utils import parse_json
from livestreamer.stream import HTTPStream

ROOM_API = "http://www.panda.tv/api_room_v2?roomid="
SD_URL_PATTERN = "http://pl{0}.live.panda.tv/live_panda/{1}.flv{2}"
HD_URL_PATTERN = "http://pl{0}.live.panda.tv/live_panda/{1}_mid.flv{2}"
OD_URL_PATTERN = "http://pl{0}.live.panda.tv/live_panda/{1}_small.flv{2}"

_url_re = re.compile("http(s)?://(\w+.)?panda.tv/(?P<channel>[^/&?]+)")

_room_schema = validate.Schema(
    {
        "data": validate.any(
            validate.text,
            validate.all(
                dict,
                {
                    "videoinfo": validate.any(
                        validate.text,
                        {
                            "room_key": validate.text,
                            "plflag": validate.text,
                            "plflag_list": validate.all(
                                validate.transform(parse_json),
                                {
                                    validate.optional("auth"): {
                                        "sign": validate.text,
                                        "rid": validate.text,
                                        "time": validate.text
                                    }
                                }
                            ),
                            "status": validate.text,
                            "stream_addr": {
                                "HD": validate.text,
                                "OD": validate.text,
                                "SD": validate.text
                            }
                        }
                    )
                }
            )
        )
    },
    validate.get("data")
)


class pandatv(Plugin):
    @classmethod
    def can_handle_url(self, url):
        return _url_re.match(url)

    def _get_streams(self):
        match = _url_re.match(self.url)
        channel = match.group("channel")

        url = ROOM_API + channel
        res = http.get(url)
        data = http.json(res, schema=_room_schema)
        if not isinstance(data, dict):
            self.logger.error("Please Check PandaTV Room API")
            return
    
        videoinfo = data.get('videoinfo')

        if not videoinfo or not videoinfo.get('status'):
            self.logger.error("Please Check PandaTV Room API")
            return
    
        if videoinfo.get('status') != '2':
            self.logger.info("Channel offline now!")
            return

        streams = {}
        plflag = videoinfo.get('plflag')
        if not plflag or not '_' in plflag:
            self.logger.error("Please Check PandaTV Room API")
            return
        plflag = plflag.split('_')[1]
        room_key = videoinfo.get('room_key')

        if "auth" in data['videoinfo']["plflag_list"]:
            auth = "?sign={0}&ts={1}&rid={2}".format(data['videoinfo']["plflag_list"]["auth"]["sign"], data['videoinfo']["plflag_list"]["auth"]["time"], data['videoinfo']["plflag_list"]["auth"]["rid"])
        else:
            auth = ""

        # SD(Super high Definition) has higher quality than HD(High Definition) which
        # conflict with existing code, use ehq and hq instead.
        stream_addr = videoinfo.get('stream_addr')
    
        if stream_addr and stream_addr.get('SD') == '1':
            streams['ehq'] = HTTPStream(self.session, SD_URL_PATTERN.format(plflag, room_key, auth))

        if stream_addr and stream_addr.get('HD') == '1':
            streams['hq'] = HTTPStream(self.session, HD_URL_PATTERN.format(plflag, room_key, auth))


        if stream_addr and stream_addr.get('OD') == '1':
            streams['sq'] = HTTPStream(self.session, OD_URL_PATTERN.format(plflag, room_key, auth))

        return streams

__plugin__ = pandatv

