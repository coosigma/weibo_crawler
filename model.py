import json

class weibo(object):
    def __init__(self, uid=None, message="", date=None, shares=None, comments=None, likes=None):
        self.uid = uid
        self.message = message
        self.date = date
        self.shares = shares
        self.comments = comments
        self.likes = likes

    def get_data(self):
        return {
            self.date : {
                'message': self.message,
                'shares': self.shares,
                'commnet': self.comments,
                'likes': self.likes
            }
        }

    def get_json(self):
        data = self.get_data()
        return json.dumps(data)
        
    def write_to_file(self, fh):
        text = self.get_json()
        fh.write(text+"\n")
