#!/usr/bin/env python
import requests
import json
import time
import datetime
import logging

# this monitors your kiln stats every N seconds
# if X checks fail, an alert is sent to a slack channel
# configure an incoming web hook on the slack channel
# set slack_hook_url to that

logging.basicConfig(filename="kiln-watcher.log",level=logging.INFO)
log = logging.getLogger(__name__)

class Watcher(object):

    def __init__(self,kiln_url,slack_hook_url,bad_check_limit=6,temp_error_limit=10,sleepfor=10):
        self.kiln_url = kiln_url
        self.slack_hook_url = slack_hook_url
        self.bad_check_limit = bad_check_limit
        self.temp_error_limit = temp_error_limit
        self.sleepfor = sleepfor
        self.bad_checks = 0
        self.stats = {}
        self.last_state = 'IDLE'
        self.has_alerted_temperature = False

    def get_stats(self):
        try:
            r = requests.get(self.kiln_url,timeout=1)
            return r.json()
        except requests.exceptions.Timeout:
            log.error("network timeout. check kiln_url and port.")
            return {}
        except requests.exceptions.ConnectionError:
            log.error("network connection error. check kiln_url and port.")
            return {}
        except:
            return {}

    def send_alert(self,msg):
        log.error("sending alert: %s" % msg)
        try:
            r = requests.post(self.slack_hook_url, json={'text': msg })
        except:
            pass

    def has_errors(self):
        if 'state' in self.stats:
            if self.stats['state'] == 'IDLE':
                return False
        if 'time' not in self.stats:
            log.error("no data")
            return True
        if 'err' in self.stats:
            if abs(self.stats['err']) > self.temp_error_limit:
                log.error("temp out of whack %0.2f" % self.stats['err'])
                return True
        return False

    def has_finished(self):
        if 'state' in self.stats:
            if self.stats['state'] == 'DONE':
                return True
        return False

    def run(self):
        log.info("started watching %s" % self.kiln_url)
        self.stats = self.get_stats()
        if 'state' in self.stats:
            self.last_state = self.stats['state']

        while(True):
            self.stats = self.get_stats()
            # 'cost': self.cost,
            # 'runtime': self.runtime,
            # 'temperature': temp,
            # 'target': self.target,
            # 'state': self.state,
            # 'heat': self.heat,
            # 'heat_rate': self.heat_rate,
            # 'totaltime': self.totaltime,
            # 'kwh_rate': config.kwh_rate,
            # 'currency_type': config.currency_type,
            # 'profile': self.profile.name if self.profile else None,
            # 'pidstats': self.pid.pidstats,
            # 'catching_up': self.catching_up,

            if self.has_finished(): 
                if self.last_state != 'DONE':
                    self.last_state = 'DONE'
                    self.send_alert("Kiln has finished it's run.")
                    time.sleep(self.sleepfor)

                if 'temperature' in self.stats:
                    if self.stats['temperature'] < 200 and not self.has_alerted_temperature:
                        self.send_alert("Kiln is below 200º and can be opened I guess...")
                        self.has_alerted_temperature = True

                time.sleep(self.sleepfor)
                continue

            else:
                self.has_alerted_temperature = False


            if self.has_errors():
                self.bad_checks = self.bad_checks + 1
            else:
                try:
                    log.info("OK temp=%0.2f target=%0.2f error=%0.2f" % (self.stats['ispoint'],self.stats['setpoint'],self.stats['err']))
                except:
                    pass

            if self.bad_checks >= self.bad_check_limit:
                msg = "error kiln needs help. %s" % json.dumps(self.stats,indent=2, sort_keys=True)
                self.send_alert(msg)
                self.bad_checks = 0

            if 'state' in self.stats:
                self.last_state = self.stats['state']

            time.sleep(self.sleepfor)

if __name__ == "__main__":

    watcher = Watcher(
        kiln_url = "http://kiln.local:80/api/stats",
        slack_hook_url = "https://hooks.slack.com/services/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",
        bad_check_limit = 6,
        temp_error_limit = 10,
        sleepfor = 10 )

    watcher.run()
