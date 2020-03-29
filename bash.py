import json
import traceback

import fire
import requests


def list():
    try:
        r = requests.post("http://api.devluoxin.cn/api/notify/get_job_list")
        if r.status_code == 200:
            try:
                d = r.json()
                for job in d:
                    print(job)
            except:
                print(r.text)
        else:
            print(r.text)
    except:
        traceback.print_exc()


def add(t=0, ts=0, msg=""):
    if t == 0:
        print(
            """
        t = 1: 一次性提醒，ts传入时间戳
        t = 2: 间隔提醒，ts传入间隔秒数
        
        msg: 提醒内容
        """
        )
    else:
        body = {
            "type": t,
            "msg": msg,
        }
        if t == 1:
            body["remind_at"] = ts
        elif t == 2:
            body["interval"] = ts

        try:
            print(
                requests.post(
                    "http://api.devluoxin.cn/api/notify/add_job", json=body
                ).text
            )
        except:
            traceback.print_exc()


if __name__ == "__main__":
    fire.Fire()
