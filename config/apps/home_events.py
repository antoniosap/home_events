#
# Home Events App
#
# notes:
# launch: appdaemon -c `pwd`/config  ---> monitor url: http://localhost:5050
#
# MONITOR MQTT:
# mosquitto_sub -h 192.168.147.1 -t ha/tts/picotts_say
#
import json
from datetime import datetime, timedelta
import appdaemon.plugins.hass.hassapi as hass
import appdaemon.plugins.mqtt.mqttapi as mqtt

# globals def
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
# sensors
ENABLE_TC_EXTERNAL = False
# TC_EXTERNAL_ID = "sensor.ewelink_th01_b0071325_temperature"   guasto 4.9.2023
TC_EXTERNAL_ID = "sensor.sonoff_th_am2301_temperature"
# external lux meter
ENABLE_EXTERNAL_LUX_METER = False
LUX_ID = 'sensor.home_lux_tsl2561_illuminance'
# home zones
ENABLE_ZONES = True
ZONES_ID = {
    "binary_sensor.ewelink_ms01_pir_bagno_ias_zone": "PIR BAGNO",
    "binary_sensor.ewelink_ms01_pir_ias_zone": "PIR INGRESSO",
    "binary_sensor.ewelink_pir02_iaszone": "PIR CUCINA",
    "binary_sensor.ewelink_pir03_motion": "PIR LAB",
    "binary_sensor.ewelink_ds01_iaszone": "SW_PORTA_INGRESSO",
    "binary_sensor.ewelink_ds01_a_iaszone": "SW_PORTA_CUCINA",
}
# tts speaker
HA_MEDIA_PLAYER_ID = "media_player.mopidy"
HA_TTS_SERVICE_TOPIC = "ha/tts/picotts_say"


def time_speaker(tm):
    if tm.minute == 0:
        return tm.strftime("%H")
    else:
        return tm.strftime("%H e %M").replace(' e 0', ' e ')


class HomeEvents(mqtt.Mqtt):
    tc_ext = 0
    lux_check_points = [0, 1, 2, 5, 7.5, 10, 20, 30, 40, 50, 100, 200, 500, 750, 1000, 2000, 5000, 7500, 10000, 20000, 50000]
    lux_check_points_hist_min = [x - (x * 10 / 100.0) for x in lux_check_points]
    lux_check_points_hist_max = [x + (x * 10 / 100.0) for x in lux_check_points]
    lux_check_points_last = -1

    def initialize(self):
        # subscribing to sensor change
        # external lux meter
        if ENABLE_EXTERNAL_LUX_METER:
            self.listen_state(self.lux_state_change, LUX_ID)
        if ENABLE_TC_EXTERNAL:
            self.listen_state(self.tc_ext_state_change, TC_EXTERNAL_ID)
        if ENABLE_ZONES:
            self.listen_state(self.pir_bagno_state_change, "binary_sensor.ewelink_ms01_pir_bagno_ias_zone")
            self.listen_state(self.pir_ingresso_state_change, "binary_sensor.ewelink_ms01_pir_ias_zone")
            self.listen_state(self.pir_cucina_state_change, "binary_sensor.ewelink_pir02_iaszone")
            self.listen_state(self.pir_lab_state_change, "binary_sensor.ewelink_pir03_motion")
            self.listen_state(self.sw_porta_ingresso_state_change, "binary_sensor.ewelink_ds01_iaszone")
            self.listen_state(self.sw_porta_cucina_state_change, "binary_sensor.ewelink_ds01_a_iaszone")

    def lux_state_change(self, entity, attribute, old, new, kwargs):
        # self.log(f"lux: {new}")
        lux = float(new)
        now = datetime.now()
        message = None
        for i, v in enumerate(self.lux_check_points):
            if self.lux_check_points_hist_min[i] <= lux <= self.lux_check_points_hist_max[i]:
                if self.lux_check_points_last != v:
                    self.lux_check_points_last = v
                    if v == 0:
                        message = f"buio alle {time_speaker(now)}"
                    else:
                        message = f"luce {int(lux)} alle {time_speaker(now)}"
                    self.log(f"lux meter message: {message}")
        if message is not None:
            # tts @ home assistant
            payload = {"time": now.strftime(TIME_FORMAT),
                       "speech": {"entity_id": HA_MEDIA_PLAYER_ID, "language": 'it-IT', "message": message}}
            self.mqtt_publish(HA_TTS_SERVICE_TOPIC, json.dumps(payload))

    def tc_ext_state_change(self, entity, attribute, old, new, kwargs):
        # self.log(f"TC ext: {new}")
        if new != 'unavailable':
            tc_ext_new = round(float(new) * 2) / 2.0
            if tc_ext_new != self.tc_ext:
                self.tc_ext = tc_ext_new
                # self.log(f"tc_ext_state_change: {self.tc_ext}")
                now = datetime.now()
                # tts @ home assistant
                message = f"sono {str(tc_ext_new).replace('.0', '')} gradi alle {time_speaker(now)}"
                payload = {"time": now.strftime(TIME_FORMAT),
                           "speech": {"entity_id": HA_MEDIA_PLAYER_ID, "language": 'it-IT', "message": message}}
                self.mqtt_publish(HA_TTS_SERVICE_TOPIC, json.dumps(payload))

    def pir_bagno_state_change(self, entity, attribute, old, new, kwargs):
        self.log(f"pir_bagno_state_change: {new}")

    def pir_ingresso_state_change(self, entity, attribute, old, new, kwargs):
        self.log(f"pir_ingresso_state_change: {new}")

    def pir_cucina_state_change(self, entity, attribute, old, new, kwargs):
        self.log(f"pir_cucina_state_change: {new}")

    def pir_lab_state_change(self, entity, attribute, old, new, kwargs):
        self.log(f"pir_lab_state_change: {new}")

    def sw_porta_ingresso_state_change(self, entity, attribute, old, new, kwargs):
        self.log(f"sw_porta_ingresso_state_change: {new}")

    def sw_porta_cucina_state_change(self, entity, attribute, old, new, kwargs):
        self.log(f"sw_porta_ingresso_state_change: {new}")
