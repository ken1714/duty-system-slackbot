import json
import os
from datetime import datetime, timedelta
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
JSON_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data", "data.json")
SCHEDULED_DATE_FORMAT = "%Y/%m/%d"
LATEST_USERLIST_DATETIME = datetime.now()
USER_LIST = None


def generate_duty_info_str(duty_info):
    return " ".join([f"<@{user_id}> {scheduled_date_str}" for user_id, scheduled_date_str in duty_info.items()])


@app.command("/schedule")
def schedule_date(ack, respond, command):
    ack()
    command_str_list = command["text"].split(' ')
    help_str = "日付はYYYY/mm/dd の形式で渡してください"
    if len(command_str_list) != 1:
        respond(help_str)
        return
    try:
        date = datetime.strptime(command_str_list[0], SCHEDULED_DATE_FORMAT)
    except ValueError:
        respond(help_str)
        return
    with open(JSON_PATH, mode="r") as json_file:
        duty_info = json.load(json_file)

    with open(JSON_PATH, mode="w") as json_file:
        if len(duty_info) == 0:
            respond("先にメンバーを設定してください")
            return
        for user_id in duty_info.keys():
            duty_info[user_id] = date.strftime(SCHEDULED_DATE_FORMAT)
            date = date + timedelta(weeks=1)
        json.dump(duty_info, json_file)

    respond(f"Scheduled. {generate_duty_info_str(duty_info)}")


@app.command("/setdate")
def set_date(ack, respond, command):
    ack()
    command_list = command["text"].split(' ')
    if len(command_list) != 2:
        respond("/setdate 変更前のYYYY/mm/dd 変更後のYYYY/mm/dd の形式で渡してください。")
        return

    for date_str in command_list:
        try:
            _ = datetime.strptime(date_str, SCHEDULED_DATE_FORMAT)
        except ValueError:
            respond("日付はYYYY/mm/ddの形式で指定してください。")
            break

    original_date_str = command_list[0]
    new_date_str = command_list[1]

    with open(JSON_PATH, mode="r") as json_file:
        duty_info = json.load(json_file)

    with open(JSON_PATH, mode="w") as json_file:
        for user_id, scheduled_date_str in duty_info.items():
            if scheduled_date_str == original_date_str:
                duty_info[user_id] = new_date_str
                break
        json.dump(duty_info, json_file)

    respond(f"Set date. {generate_duty_info_str(duty_info)}")


@app.command("/adduser")
def add_user(ack, respond, command):
    ack()
    add_users = command["text"].split(' ')
    add_users = [add_user[1:] for add_user in add_users if add_user.startswith("@")]

    now_datetime = datetime.now()
    global LATEST_USERLIST_DATETIME
    global USER_LIST
    if (now_datetime - LATEST_USERLIST_DATETIME).days >= 1 or USER_LIST is None:
        USER_LIST = app.client.users_list()
        LATEST_USERLIST_DATETIME = now_datetime

    # TODO: implement remove function
    duty_info = dict()
    added_user_ids = list()
    with open(JSON_PATH, mode="w") as json_file:
        for add_user_name in add_users:
            for user in USER_LIST["members"]:
                user_name = user.get("name", "")
                if add_user_name == user_name:
                    user_id = user.get("id", None)
                    if user_id is None:
                        continue
                    duty_info[user_id] = None
                    added_user_ids.append(user_id)
        json.dump(duty_info, json_file)

    respond(f"Added users. {generate_duty_info_str(duty_info)}")


@app.command("/echo")
def show_duty_info(ack, respond):
    ack()
    with open(JSON_PATH, mode="r") as json_file:
        duty_info = json.load(json_file)
        if len(duty_info) > 0:
            respond(generate_duty_info_str(duty_info))
        else:
            respond("議事録当番は設定されていません。")


if __name__ == "__main__":
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, mode="w") as json_file:
            json.dump(dict(), json_file)
    try:
        SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
    except KeyboardInterrupt:
        print("Exit app")
