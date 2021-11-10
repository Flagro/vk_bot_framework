import json
import os.path
import datetime

class NextEvent:
    def __init__(self, t, cid, txt):
        self.timer = t
        self.chat_id = cid
        self.text = txt

class Event:
    def __init__(self, dttime, cid, txt):
        self.time = dttime
        self.chat_id = cid
        self.text = txt

class ServerSchedule:
    def __init__(self, schedule_json_path):
        self.path = schedule_json_path

    def get_first(self):
        schedule_dict = {}
        with open(self.path) as schedule_json:
            schedule_dict = json.load(schedule_json)
        now_time = datetime.datetime.now()
        it_time = datetime.datetime.now()
        time_list = []
        cur_ans = None
        for key, value in schedule_dict.items():
            if value["type"] == "daily":
                for t in value["time"]:
                    test_time = datetime.datetime.strptime(t, "%I:%M%p")
                    it_time = it_time.replace(hour=test_time.hour,minute=test_time.minute, second=test_time.second)
                    time1 = it_time+datetime.timedelta(days=0)
                    time2 = it_time+datetime.timedelta(days=1)
                    if now_time < time1:
                        if cur_ans == None or cur_ans.time > time1:
                            cur_ans = Event(dttime=time1,cid=value["chat_id"], txt=value["text"])
                    if now_time < time2:
                        if cur_ans == None or cur_ans.time > time2:
                            cur_ans = Event(dttime=time2,cid=value["chat_id"], txt=value["text"])
            else:
                return None
        if cur_ans==None:
            return None
        return NextEvent(t=(cur_ans.time - now_time).total_seconds(), cid=cur_ans.chat_id, txt=cur_ans.text)
