import vk_api
from vk_api import VkUpload
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import json
from random import random
import os.path
import datetime
from vkmessage import VKmsgOut, VKmsgIn, VKmsgIn_from_text
from serverschedule import ServerSchedule
import time
import requests
import threading
import importlib

def get_random_id():
    return round((random() * (10 ** 10)))

class BotServer:
    def __init__(self, group_json_path, bot_json_path, schedule_json_path):
        with open(group_json_path) as group_json:
            group_dict = json.load(group_json)
            self.group_token = group_dict["group_token"]
            self.group_id = group_dict["group_id"]

        self.vk_session = vk_api.VkApi(token=self.group_token)

        self.upload = VkUpload(self.vk_session)

        self.longpoll = VkBotLongPoll(self.vk_session, self.group_id)
    
        self.vk = self.vk_session.get_api()

        self.schedule = ServerSchedule(schedule_json_path)

        print(str(datetime.datetime.now()) + " " + "Importing bot modules...")
        bot_dict = None
        with open(bot_json_path) as bot_json:
            bot_dict = json.load(bot_json)
        importlib.invalidate_caches()
        self.bot_modules = {}
        self.no_trigger_module = str(bot_dict["no_trigger_module"])
        py_module_prefix = str(bot_dict["bots_source_py_module_prefix"])
        for key, item in bot_dict["vk_bots"].items():
            module_path = py_module_prefix + str(item["python_module"])
            module = importlib.import_module(module_path)
            class_name = str(item["class_name"])
            class_instance = getattr(module, class_name)(item["bot_files"])
            trigger_words = item["trigger_words"]
            self.bot_modules[key] = {"class":class_instance, "trigger_words":trigger_words}
        print(str(datetime.datetime.now()) + " " + "Bot modules successfully imported.\nImported modules:")
        for key in list(self.bot_modules.keys()):
            print("+" + str(key))

        print(str(datetime.datetime.now()) + " " + "Bot is ready")
    
    def get_reply(self, msg):
        text = msg.text
        if text == "!botserver stop":
            return VKmsgOut(txt="!botserverstop")
        elif text == "!botserver time":
            return VKmsgOut(txt="!botservertime")
        for word in text.split():
            for key, item in self.bot_modules.items():
                for trigger_word in item["trigger_words"]:
                    if word.lower() == trigger_word:
                        text_arr = text.split()
                        text_arr.remove(trigger_word)
                        text_for_bot = " ".join(text_arr)
                        msg.text = text_for_bot
                        return item["class"].get_reply(msg)
        for key, item in self.bot_modules.items():
            if key==self.no_trigger_module:
                return item["class"].get_reply(msg)
        return VKmsgOut()

    def preprocess_reply(self, text, event):
        if "__first_name__" in text: 
            first_name = "Pepega"
            if event!=None:
                try:
                    user_id = event.message["from_id"]
                    user = self.vk.users.get(user_ids=(user_id))[0]
                    first_name = "@id" + str(user_id) + " (" + str(user["first_name"]) + ")"
                except vk_api.exceptions.ApiError:
                    pass
            text = text.replace("__first_name__", first_name)
        if "__last_name__" in text:
            last_name = "Guy"
            if event!=None:
                try:
                    user_id = event.message["from_id"]
                    user = self.vk.users.get(user_ids=(user_id))[0]
                    last_name = "@id" + str(user_id) + " (" + str(user["last_name"]) + ")"
                except vk_api.exceptions.ApiError:
                    pass
            text = text.replace("__last_name__", last_name)
        return text

    def send_msg_in_chat(self, chat_id, msg):
        text, atch = msg.get_text_atch(self.upload)
        self.vk.messages.send(
            message=text,
            dont_parse_links="0",
            chat_id=chat_id,
            attachment=atch,
            random_id=get_random_id()
        )

    def eventplanner_thread(self):
        print(str(datetime.datetime.now()) + " " + "Event planner is now working")
        while True:
            next_event = self.schedule.get_first()
            print(str(datetime.datetime.now()) + " " + "Next planned msg is in " + str(int(next_event.timer)))
            sleep_time = int(next_event.timer)
            if sleep_time > 3600:
                time.sleep(3600)
                continue
            time.sleep(sleep_time)
            print(str(datetime.datetime.now()) + " " + "Sending planned message to the " + str(next_event.chat_id))
            msg = self.get_reply(msg=VKmsgIn_from_text(next_event.text))
            reply = self.preprocess_reply(msg.text, event=None)
            msg.text = reply
            self.send_msg_in_chat(next_event.chat_id, msg)
            time.sleep(5)
        print(str(datetime.datetime.now()) + " " + "Event planner stopping working")

    def longpolling(self):
        # main thread
        print(str(datetime.datetime.now()) + " " + "Started longpolling")
        for event in self.longpoll.listen():
            print(str(datetime.datetime.now()) + " " + "New event:", end=" ")
            exit_event = self.process_event(event)
            if exit_event:
                print(str(datetime.datetime.now()) + " " + "Stopping longpolling")
                return 1
        return 0

    def listen(self):
        if threading.active_count() == 1:
            ep = threading.Thread(target=self.eventplanner_thread, daemon=True)
            ep.start()
        stop = self.longpolling()
        if stop:
            return 1
        return 0

    def process_event(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.from_chat:
                print("New msg from chat" + " " + str(event.chat_id))
                incoming_msg = VKmsgIn(event, self.vk)
                reply = self.get_reply(incoming_msg)
                if reply.text != None:
                    reply.text = self.preprocess_reply(reply.text, event)
                if reply.text == "!botserverstop":
                    return 1
                elif reply.text == "!botservertime":
                    reply.text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if not reply.isempty():
                    self.send_msg_in_chat(event.chat_id, reply)
        return 0

def main():
    while True:
        try:
            bot = BotServer("./group.json", "./vkbot.json", "./schedule.json")
            stop = bot.listen()
            if stop:
                break
        except requests.exceptions.RequestException:
            print("Reconnecting to VK servers")
            time.sleep(10)

if __name__ == "__main__":
    main()
