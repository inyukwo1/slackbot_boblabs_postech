from slacker import Slacker
from typing import Dict
import requests
import argparse
import time
from time import sleep
import json

# TODO 학생식당, 교직원식당, 푸드코트, RIST 추가 필요


def post_slackbot(slack_token: str, menu_obj: Dict) -> None:
    slack = Slacker(slack_token)

    # Send a message to #general channel
    slack.chat.post_message('#밥', '오늘의 식단을 소개합니다.')

    # 인재개발원
    inje_obj = menu_obj["stores"][2]
    slack.chat.post_message('#밥', '인재개발원-아침-'+inje_obj["menus"][0]["name"] + ":::" +
                            inje_obj["menus"][0]["description"])
    slack.chat.post_message('#밥', '인재개발원-점심-'+inje_obj["menus"][1]["name"] + ":::" +
                            inje_obj["menus"][1]["description"])
    slack.chat.post_message('#밥', '인재개발원-점심-'+inje_obj["menus"][2]["name"] + ":::" +
                            inje_obj["menus"][2]["description"])
    slack.chat.post_message('#밥', '인재개발원-저녁-'+inje_obj["menus"][3]["name"] + ":::" +
                            inje_obj["menus"][3]["description"])

    # 가속기연구소
    gasok_obj = menu_obj["stores"][3]
    tmp_file_loc = "tmp.jpg"
    with open(tmp_file_loc, 'wb') as f:
        resp = requests.get(gasok_obj["menus"][0]["description"], verify=False)
        f.write(resp.content)
    slack.chat.post_message('#밥', "아래는 가속기연구소 식단입니다.")
    # TODO 아래 업로드가 bot이 아니라 user 이름으로 올라갑니다.
    slack.files.upload(tmp_file_loc, channels='#밥', title="가속기연구소 식단")


def get_menu(boblab_token: str) -> Dict:
    API_HOST = 'https://bablabs.com/openapi/v1/'
    POSTECH_TOKEN = '3hXYy5crHG'
    headers = {'Accesstoken': boblab_token}

    query = {"date": time.strftime("%Y-%m-%d")}
    resp = requests.get(API_HOST + '/campuses/' + POSTECH_TOKEN + '/stores', params=query, headers=headers)
    obj = json.loads(resp.text)
    return obj


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gets tokens')
    parser.add_argument("slack_token", help="slack token", type=str)
    parser.add_argument("boblab_token", help="boblab token", type=str)
    args = parser.parse_args()
    while True:
        # 하루 한 번 아침 9시쯤 콜합니다.
        if time.localtime().tm_hour == 9:
            menu_obj = get_menu(args.boblab_token)
            post_slackbot(args.slack_token, menu_obj)
        sleep(3600)
