import argparse
import json
import os
from datetime import datetime, timedelta
from slack_sdk import WebClient
from run import JSON_PATH, SCHEDULED_DATE_FORMAT


def get_notice_channel_id(client: WebClient, notice_channel_name: str):
    channel_info = client.conversations_list(types="public_channel, private_channel")
    for channel in channel_info["channels"]:
        if channel["name"] == notice_channel_name:
            return channel["id"]

    return None


def notice(client: WebClient, notice_channel_id: str):
    now_datetime = datetime.now()

    with open(JSON_PATH, mode="r") as json_file:
        duty_info = json.load(json_file)
        for user_id, scheduled_date_str in duty_info.items():
            scheduled_datetime = datetime.strptime(scheduled_date_str, SCHEDULED_DATE_FORMAT)
            if 0 <= (scheduled_datetime - now_datetime).days < 1:
                client.chat_postMessage(channel=notice_channel_id, text=f"<@{user_id}> {scheduled_date_str}の会議の議事録当番です。議事録ファイルを準備してください。")


def update_scheduled_date(schedule_interval_days: int):
    now_datetime = datetime.now()
    
    with open(JSON_PATH, mode="r") as json_file:
        duty_info = json.load(json_file)

    with open(JSON_PATH, mode="w") as json_file:
        # Search latest scheduled date
        latest_timestamp = 0
        for user_id, scheduled_date_str in duty_info.items():
            scheduled_timestamp = datetime.strptime(scheduled_date_str, SCHEDULED_DATE_FORMAT).timestamp()
            if scheduled_timestamp > latest_timestamp:
                latest_timestamp = scheduled_timestamp

        # Update scheduled date
        latest_datetime = datetime.fromtimestamp(latest_timestamp) + timedelta(days=schedule_interval_days)
        for user_id, scheduled_date_str in duty_info.items():
            scheduled_timestamp = datetime.strptime(scheduled_date_str, SCHEDULED_DATE_FORMAT).timestamp()
            if scheduled_timestamp < now_datetime.timestamp():
                duty_info[user_id] = latest_datetime.strftime(SCHEDULED_DATE_FORMAT)
        json.dump(duty_info, json_file)


def main(notice_channel_name, schedule_interval_days):
    # Slack app
    slack_token = os.environ["SLACK_BOT_TOKEN"]
    client = WebClient(token=slack_token)

    # Notice
    notice_channel_id = get_notice_channel_id(client, notice_channel_name)
    if notice_channel_id is not None:
        notice(client, notice_channel_id)

    # Update
    update_scheduled_date(schedule_interval_days)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notice_channel_name", type=str)
    parser.add_argument("schedule_interval_days", type=int)

    args = parser.parse_args()
    main(args.notice_channel_name, args.schedule_interval_days)
