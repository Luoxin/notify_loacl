import datetime
import json
import threading
import time
import traceback
import uuid as uu

from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
from tinydb import TinyDB
from tinydb.database import Document
from win10toast import ToastNotifier

from variable_manager import VariableManager

app = Flask("notify")


def gen_uuid() -> str:
    return uu.uuid4().hex


class Remind(BackgroundScheduler):
    def __init__(self):
        self.toast = ToastNotifier()
        super().__init__()

        threading.Thread(target=self.start, daemon=True).start()

        self.db = TinyDB("./remind.d")

        job_list = self.db.all()
        for job in job_list:
            if self.add(job) == "repeat job id":
                print(type(job))
                self.db.remove(doc_ids=[job.doc_id])

    def notify(self, msg: str = "新的提醒"):
        self.toast.show_toast("消息提醒", msg=msg, threaded=True, duration=10)

    def task(self, task_desc):
        self.notify(task_desc)

    def add(self, data: (dict, Document)):
        try:
            job = VariableManager(data)

            msg = job.get_val_str("msg", )
            if msg == "":
                return "miss msg"

            job_id = job.get_val_str("job_id", default=gen_uuid())

            if self.get_job(job_id=job_id) is not None:
                return "repeat job id"

            job.add_val("job_id", job_id)

            t = job.get_val_int("type")
            if t == 0:
                return "miss type"

            elif t == 1:  # 一次性提醒
                now = int(time.time())
                remind_at = job.get_val_int("remind_at")
                if remind_at < now:
                    return "invalid remind at"

                self.add_job(
                    self.task,
                    trigger="date",
                    next_run_time=datetime.datetime.fromtimestamp(remind_at),
                    id=job_id,
                    args=[msg],
                )

            elif t == 2:  # 间隔提醒
                interval = job.get_val_float("interval")
                if interval <= 0:
                    return "invalid interval"

                self.add_job(
                    self.task,
                    trigger="interval",
                    seconds=interval,
                    id=job_id,
                    args=[msg],
                )

            if not isinstance(data, Document):
                self.db.insert(job.get_val_all())
            return "OK"
        except ConflictingIdError:
            return "repeat job id"
        except:
            traceback.print_exc()
            return traceback.format_exc()


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
    return remind.add(request.json)


@app.route("/api/notify/get_job_list", methods=["POST"])
def get_job_list():
    job_list = []

    try:
        for job in remind.get_jobs():
            if job.args.__len__() > 0:
                job_list.append(
                    {
                        "job_id": job.id,
                        "title": job.args[0],
                        "next run time": job.next_run_time,
                    }
                )
    except:
        traceback.print_exc()
        return traceback.format_exc()

    return json.dumps(job_list)


@app.route("/api/notify/del_job", methods=["POST"])
def del_job():
    try:
        req = VariableManager(request.json)

        remind.remove_job(job_id=req.get_val_str("id", default=""))
        return "OK"
    except JobLookupError:
        return "job is not exist"
    except:
        traceback.print_exc()
        return traceback.format_exc()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8801, debug=True)
