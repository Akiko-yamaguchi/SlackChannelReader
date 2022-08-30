# Copyright (C) 2022 Daijiro Fukuda <fukuda@clear-code.com>

# This file is part of SlackChannelReader.

# SlackChannelReader is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# SlackChannelReader is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import json
import csv
from datetime import datetime
from urllib.request import Request, urlopen
from typing import List 


class SlackApi:
    def __init__(self, token: str):
        self._token = token

    def conversations_history(self, channel_id: str, limit: int) -> dict:
        url = f"https://slack.com/api/conversations.history?channel={channel_id}&limit={limit}"
        response = urlopen(Request(url, headers=self.__headers()))
        return json.loads(response.read().decode())

    def conversations_replies(self, channel_id: str, thread_ts: str) -> dict:
        url = f"https://slack.com/api/conversations.replies?channel={channel_id}&ts={thread_ts}"
        response = urlopen(Request(url, headers=self.__headers()))
        return json.loads(response.read().decode())

    def __headers(self) -> dict:
        return {
            'Authorization': f"Bearer {self._token}",
            'Content-Type': 'application/json',
        }


class Message:
    def __init__(self, text: str, user: str, ts: str):
        self.text = text
        self.user = user
        self.ts = ts

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(float(self.ts))

    @property
    def datetime_str(self) -> str:
        return self.datetime.strftime("%Y-%m-%d %H:%M:%S")


class TopMessage(Message):
    def __init__(self, raw: dict):
        super(TopMessage, self).__init__(
            raw.get("text", ""),
            raw.get("user", ""),
            raw["ts"]
        )
        self.reply_count = raw.get("reply_count", 0)
        self.reply_users_count = raw.get("reply_users_count", 0)
        self.thread_ts = raw.get("thread_ts")
        self.thread_messages: List[Message] = []

    @property
    def json(self) -> dict:
        return json.dumps({
            "ts": self.ts,
            "user": self.user,
            "text": self.text,
            "reply_count": self.reply_count,
            "reply_users_count": self.reply_users_count,
            "thread_ts": self.thread_ts,
            "thread_messages": [
                {
                    "ts": tm.ts,
                    "user": tm.user,
                    "text": tm.text,
                } for tm in self.thread_messages
            ],
        })

    @property
    def csv_rows(self) -> List[List[any]]:
        if not len(self.thread_messages):
            return [[self.datetime_str, self.user, self.text]]
        return [[tm.datetime_str, tm.user, tm.text] for tm in self.thread_messages]


class SlackChannelReader:
    def __init__(self, token: str, channel_id: str, limit: int=1000):
        self._token = token
        self._channel_id = channel_id
        self._limit = limit
        self._api = SlackApi(token)

    def read(self) -> List[TopMessage]:
        history = self._api.conversations_history(self._channel_id, self._limit)
        top_messages = [TopMessage(raw) for raw in history["messages"]]
        for mes in top_messages:
            self.__merge_thread_messages(mes)
        return top_messages

    def __merge_thread_messages(self, top_message: TopMessage):
        if top_message.thread_ts is None:
            return
        replies = self._api.conversations_replies(self._channel_id, top_message.thread_ts)
        if replies.get("ok", False):
            top_message.thread_messages.extend(
                Message(raw["text"], raw["user"], raw["ts"]) for raw in replies["messages"]
            )


class MessageSerializer:
    def dump_json(self, top_messages: List[TopMessage], filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([m.json for m in top_messages], f, indent=4)

    def parse_json_raw(self, filepath: str) -> List[dict]:
        with open(filepath, "r", encoding="utf-8") as f:
            return [json.loads(j) for j in json.load(f)]

    def parse_json(self, filepath: str) -> List[TopMessage]:
        top_messages = []
        raw_messages = self.parse_json_raw(filepath)
        for rm in raw_messages:
            top_message = TopMessage(rm)
            top_message.thread_messages.extend(
                [Message(tm["text"], tm["user"], tm["ts"]) for tm in rm["thread_messages"]]
            )
            top_messages.append(top_message)
        return top_messages

    def dump_csv(self, top_messages: List[TopMessage], filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            writer = csv.writer(f)
            for m in top_messages:
                writer.writerows(m.csv_rows)
