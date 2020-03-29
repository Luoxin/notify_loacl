import datetime
import threading
import time
import traceback
import uuid as uu
from typing import Any

from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from pydantic import BaseModel
from tinydb import TinyDB
from tinydb.database import Document
from win10toast import ToastNotifier


class Job(BaseModel):
    id: str = ""
    msg: str = ""
    type: int = 0
    remind_at: int = 0
    interval: int = 0


class Response(BaseModel):
    errcode: int = 0
    errmsg: str = ""
    data: Any = None

    def err(self, errcode: int, errmsg: str = "") -> BaseModel:
        self.errcode = errcode
        self.errmsg = errmsg
        return self

    def r(self, data: Any) -> BaseModel:
        self.errcode = 0
        self.errmsg = ""
        self.data = data
        return self


def gen_uuid() -> str:
    return uu.uuid4().hex


def _doc2job(data: Document) -> Job:
    return Job(**data)


class Remind(BackgroundScheduler):
    def __init__(self):
        self.toast = ToastNotifier()
        super().__init__()

        threading.Thread(target=self.start, daemon=True).start()

        self.db = TinyDB("./remind.d")

        job_list = self.db.all()
        for job in job_list:
            if self.add(job).dict().get("id") not in [0, None]:
                self.db.remove(doc_ids=[job.doc_id])

    def notify(self, msg: str = "新的提醒"):
        self.toast.show_toast("消息提醒", msg=msg, threaded=True, duration=10)

    def task(self, task_desc):
        self.notify(task_desc)

    def add(self, job: (Job, Document), persistence: bool = False) -> BaseModel:
        rsp = Response()
        try:
            if isinstance(job, Document):
                job = _doc2job(job)

            if job.msg == "":
                return rsp.err(1001, "miss msg")

            if job.id == "":
                job.id = gen_uuid()

            if self.get_job(job_id=job.id) is not None:
                return rsp.err(1001, "repeat job id")

            now = int(time.time())
            if job.type == 0:
                return rsp.err(1001, "miss type")

            elif job.type == 1:  # 一次性提醒
                if job.remind_at < now:
                    return rsp.err(1001, "invalid remind at")

                self.add_job(
                    self.task,
                    trigger="date",
                    next_run_time=datetime.datetime.fromtimestamp(job.remind_at),
                    id=job.id,
                    args=[job.msg],
                )

            elif job.type == 2:  # 间隔提醒
                if job.remind_at == 0:
                    job.remind_at = None
                elif job.remind_at < now:
                    return rsp.err(1001, "invalid remind at")

                if job.interval <= 0:
                    return rsp.err(1001, "invalid interval")

                self.add_job(
                    self.task,
                    trigger="interval",
                    next_run_time=datetime.datetime.fromtimestamp(job.remind_at),
                    seconds=job.interval,
                    id=job.id,
                    args=[job.msg],
                )

            if persistence:
                self.db.insert(job.dict())
            return rsp.r({"job": job})
        except ConflictingIdError:
            return rsp.err(1003, "repeat job id")
        except:
            return rsp.err(-1, traceback.format_exc())


remind = Remind()
app = FastAPI(title="notify", version="0.0.1.10")


@app.post(path="/api/notify/add_job")
def add_job(add_job: Job):
    return remind.add(add_job, True)


@app.post(path="/api/notify/get_job_list")
def get_job_list():
    job_list = []
    rsp = Response()

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
        return rsp.r({"list": job_list})
    except:
        return rsp.err(-1, traceback.format_exc())


@app.post(path="/api/notify/del_job/id")
def del_job(id: str):
    rsp = Response()
    try:
        remind.remove_job(job_id=id)
        return rsp.r()
    except JobLookupError:
        return rsp.err(1003,"job is not exist")
    except:
        return rsp.err(-1, traceback.format_exc())
