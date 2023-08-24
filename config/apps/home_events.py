#
# Home Events App
#
# Args:
#
# notes:
# launch: appdaemon -c `pwd`/config  ---> monitor url: http://localhost:5050
#
import json
from datetime import datetime, timedelta
import appdaemon.plugins.hass.hassapi as hass
import appdaemon.plugins.mqtt.mqttapi as mqtt

# globals def
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
# sensors
LUX_ID = 'sensor.home_lux_tsl2561_illuminance'
TC_EXTERNAL_ID = "sensor.ewelink_th01_b0071325_temperature"
# tts speaker
HA_MEDIA_PLAYER_ID = "media_player.mopidy"
HA_TTS_SERVICE_TOPIC = "ha/tts/picotts_say"


def time_speaker(tm):
    if tm.minute == 0:
        return tm.strftime("%H")
    else:
        return tm.strftime("%H e %M").replace(' e 0', ' e ')


class HomeEvents(mqtt.Mqtt):
    lux = 0
    tc_ext = 0

    def initialize(self):
        # subscribing to sensor change
        self.listen_state(self.lux_state_change, LUX_ID)
        self.listen_state(self.tc_ext_state_change, TC_EXTERNAL_ID)

    def lux_state_change(self, entity, attribute, old, new, kwargs):
        # self.log(f"lux: {new}")
        self.lux = new

    def tc_ext_state_change(self, entity, attribute, old, new, kwargs):
        # self.log(f"TC ext: {new}")
        tc_ext_new = round(float(new) * 2) / 2.0
        if tc_ext_new != self.tc_ext:
            self.tc_ext = tc_ext_new
            # self.log(f"tc_ext_state_change: {self.tc_ext}")
            now = datetime.now()
            # tts @ home assistant
            message = f"{str(tc_ext_new).replace('.0', '')} gradi alle {time_speaker(now)}"
            payload = {"time": now.strftime(TIME_FORMAT),
                       "speech": {"entity_id": HA_MEDIA_PLAYER_ID, "language": 'it-IT', "message": message}}
            self.mqtt_publish(HA_TTS_SERVICE_TOPIC, json.dumps(payload))
