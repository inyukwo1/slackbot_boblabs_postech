from slacker import Slacker
from typing import Dict
import requests
import argparse
import time
from time import sleep
import json
from bs4 import BeautifulSoup
import re

# TODO 학생식당, 교직원식당, 푸드코트, RIST 추가 필요

def get_postech_menu(menu_obj: Dict) -> Dict:
    url = 'http://fd.postech.ac.kr/bbs/today_menu.php?bo_table=weekly'
    html = requests.get(url)
    html.encoding='utf-8'
    html = html.text
    soup = BeautifulSoup(html, 'lxml')
    tags = soup.find_all('td', class_='txtheight')
    i, obj = 0, dict()
    obj["menus"] = dict()
    for tag in tags:
        description = tag.get_text().encode('utf-8','strict')
        description = description.decode('utf-8','strict')
        iobj = dict()
        iobj["name"] = ""
        description = description.replace('\n',' ').replace('\r', ' ').replace('&',' ').replace('  ', ' ')
        description = re.sub('[a-zA-z]*', '', description).replace('"', '').replace('  ', ' ').replace('  ', ' ').replace('  ', ' ')
        iobj["description"] = description
        obj["menus"][i] = iobj
        i += 1
    menu_obj["stores"][4] = obj
    return menu_obj

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

    # POSTECH 학생 식당
    slack.chat.post_message('#밥', "아래는 POSTECH 학생식당 식단입니다.")
    student_obj = menu_obj["stores"][4]
    slack.chat.post_message('#밥', '학생식당-아침 A-'+student_obj["menus"][0]["name"] + ":::" +
                            student_obj["menus"][0]["description"])
    slack.chat.post_message('#밥', '학생식당-아침 B-'+student_obj["menus"][1]["name"] + ":::" +
                            student_obj["menus"][1]["description"])
    slack.chat.post_message('#밥', '학생식당-점심-'+student_obj["menus"][2]["name"] + ":::" +
                            student_obj["menus"][2]["description"])
    slack.chat.post_message('#밥', '학생식당-저녁-'+student_obj["menus"][3]["name"] + ":::" +
                            student_obj["menus"][3]["description"])

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
            menu_obj = get_postech_menu(menu_obj)
            post_slackbot(args.slack_token, menu_obj)
        sleep(3600)
