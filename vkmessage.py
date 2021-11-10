import vk_api

class VKmsgIn:
    def __init__(self, event=None, vk=None, user=None):
        self.first_name = "Pepega"
        self.last_name = "Guy"
        self.from_group = False
        if event!=None:
            self.text = event.message["text"]
            self.from_id = event.message["from_id"]
            try:
                user = vk.users.get(user_ids=(event.message["from_id"]))[0]
                self.first_name = "@id" + str(self.from_id) + " (" + str(user["first_name"]) + ")"
                self.last_name = "@id" + str(self.from_id) + " (" + str(user["last_name"]) + ")"
            except vk_api.exceptions.ApiError:
                self.from_group = True
        else:
            self.text=""
            self.from_id = None
            self.from_group = True


def VKmsgIn_from_text(text):
    instance = VKmsgIn()
    instance.text=text
    return instance

class VKmsgOut:
    def __init__(self, txt="", imglist=[], audlist=[], urllist=[], giflist=[], ping_user=False):
        self.text = txt
        self.imagelist = imglist
        self.audiolist = audlist
        self.urllist = urllist
        self.giflist = giflist
        self.ping_user = ping_user
    def isempty(self):
        return self.text=="" and self.imagelist==[] and self.audiolist==[] and self.urllist==[] and self.giflist==[]
    def get_text_atch(self, upload):
        text = self.text
        for el in self.urllist:
            text += "\n" + el
        atch = []
        for image in self.imagelist:
            with open("./attachments/pictures/"+image, "rb") as picture:
                photo = upload.photo_messages(picture)[0]
                atch.append(
                    "photo{}_{}".format(photo["owner_id"], photo["id"])
                )
        for audio in self.audiolist:
            #atch.append(
            #    "audio{}_{}".format(93744418, 93744418)
            #)
            pass
        #atch.append(self.urllist[0])
        attachment=','.join(atch)
        return text, attachment

def VKmsgOut_from_dict(d):
    instance = VKmsgOut()
    for key, value in d.items():
        if key == "text":
            instance.text = value
        elif key == "imagelist":
            instance.imagelist = value        
        elif key == "audiolist":
            instance.audiolist = value
        elif key == "urllist":
            instance.urllist = value
        elif key == "giflist":
            instance.giflist = value
        elif key == "ping_user":
            instance.ping_user = value
    return instance
