import datetime
import threading
import time
import traceback
import uuid as uu

from apscheduler.schedulers.background import BackgroundScheduler

from variable_manager import VariableManager
from flask import Flask, request
from win10toast import ToastNotifier

app = Flask("notify")


def gen_uuid() -> str:
    return uu.uuid4().hex


class Remind(BackgroundScheduler):
    def __init__(self):
        self.toast = ToastNotifier()
        super().__init__()
        threading.Thread(target=self.start, daemon=True).start()

    def notify(self, msg: str = "新的提醒"):
        self.toast.show_toast("消息提醒", msg=msg, threaded=True, duration=10)

    def task(self, task_desc):
        self.notify(task_desc)


remind = Remind()


@app.route("/api/notify/send", methods=["POST"])
def send():
    try:
        req = request.json

        message = req.get("message")
        if message is None or message == "":
            return "miss message"

        remind.notify(message)
        return "OK"
    except:
        return traceback.format_exc()


@app.route("/api/notify/add_job", methods=["POST"])
def add_job():
    try:
        req = VariableManager(request.json)

        msg = req.get_val_str("msg",)
        if msg == "":
            return "miss msg"

        t = req.get_val_int("type")
        if t == 0:
            return "miss type"
        elif t == 1:  # 一次性提醒
            now = int(time.time())
            remind_at = req.get_val_int("remind_at")
            if remind_at < now:
                return "invalid remind at"

            remind.add_job(
                remind.task,
                trigger="date",
                next_run_time=datetime.datetime.fromtimestamp(remind_at),
                id=gen_uuid(),
                args=[msg],
            )
        elif t == 2:  # 间隔提醒
            interval = req.get_val_float("interval")
            if interval <= 0:
                return "invalid interval"

            remind.add_job(
                remind.task,
                trigger="interval",
                seconds=interval,
                id=gen_uuid(),
                args=[msg],
            )
        return "OK"
    except:
        traceback.print_exc()
        return traceback.format_exc()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8801, debug=True)
