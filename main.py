from slacker import Slacker
from typing import Dict
import requests
import argparse
import time
from time import sleep
import json
from bs4 import BeautifulSoup
import re
from selenium import webdriver


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
        description = description.replace('\n',' ').replace('\r', ' ').replace('&',' ')
        description = re.sub('[a-zA-z]*', '', description).replace('"', '')
        description = re.sub('[\s]+', ' ', description)
        iobj["description"] = description
        obj["menus"][i] = iobj
        i += 1
    menu_obj["stores"][4] = obj
    return menu_obj


def get_food_court_menu(menu_obj: Dict) -> Dict:
    url = "http://fd.postech.ac.kr/bbs/board.php?bo_table=food_court"
    html = requests.get(url)
    html.encoding = "utf-8"
    soup = BeautifulSoup(html.text, 'lxml')
    tags = soup.find_all('td', class_='num')#href=re.compile('wr_id'))
    wr_id = int(tags[0].get_text().strip()) + 2
    url = "http://fd.postech.ac.kr/bbs/board.php?bo_table=food_court&wr_id=%d" % wr_id
    html = requests.get(url)
    html.encoding = "utf-8"
    soup = BeautifulSoup(html.text, 'lxml')
    tables = soup.find_all('table')
    contents = tables[3].find_all('td')
    j, obj = 0, dict()
    obj["menus"] = dict()
    for i in [8, 12, 13]:
        description = contents[i].get_text().replace('+',' ').replace('-',' ').replace('\n',' ').replace('\r', ' ').replace('&',' ')
        description = re.sub('[a-zA-z]*', '', description).replace('"', '')
        description = re.sub('[\s]+', ' ', description)
        iobj = dict()
        iobj["name"] = ""
        iobj["description"] = description
        obj["menus"][j] = iobj
        j += 1
    menu_obj["stores"][5] = obj
    return menu_obj


def post_slackbot(slack_token: str, menu_obj: Dict, test: bool=False) -> None:
    slack = Slacker(slack_token)
    channel_name = "#밥_dev" if test else "#밥"

    slack.chat.post_message(channel_name, '★오늘의 식단을 소개합니다★')

    inje_obj = menu_obj["stores"][2]
    slack.chat.post_message(channel_name, '♥인재개발원♥-아침-'+inje_obj["menus"][0]["name"] + ":::" +
                            inje_obj["menus"][0]["description"])
    slack.chat.post_message(channel_name, '♥인재개발원♥-점심-'+inje_obj["menus"][1]["name"] + ":::" +
                            inje_obj["menus"][1]["description"])
    slack.chat.post_message(channel_name, '♥인재개발원♥-점심-'+inje_obj["menus"][2]["name"] + ":::" +
                            inje_obj["menus"][2]["description"])
    slack.chat.post_message(channel_name, '♥인재개발원♥-저녁-'+inje_obj["menus"][3]["name"] + ":::" +
                            inje_obj["menus"][3]["description"])

    gasok_obj = menu_obj["stores"][3]
    tmp_file_loc = "tmp.jpg"
    with open(tmp_file_loc, 'wb') as f:
        resp = requests.get(gasok_obj["menus"][0]["description"], verify=False)
        f.write(resp.content)
    slack.chat.post_message(channel_name, "아래는 가속기연구소 식단입니다.")
    slack.files.upload(tmp_file_loc, channels='#밥', title="가속기연구소 식단")

    # POSTECH 학생 식당
    slack.chat.post_message(channel_name, "아래는 POSTECH 학생식당 식단입니다.")
    student_obj = menu_obj["stores"][4]
    slack.chat.post_message(channel_name, '학생식당-아침 A-'+student_obj["menus"][0]["name"] + ":::" +
                            student_obj["menus"][0]["description"])
    slack.chat.post_message(channel_name, '학생식당-아침 B-'+student_obj["menus"][1]["name"] + ":::" +
                            student_obj["menus"][1]["description"])
    slack.chat.post_message(channel_name, '학생식당-점심-'+student_obj["menus"][2]["name"] + ":::" +
                            student_obj["menus"][2]["description"])
    slack.chat.post_message(channel_name, '학생식당-저녁-'+student_obj["menus"][3]["name"] + ":::" +
                           student_obj["menus"][3]["description"])

    # POSTECH 교직원 식당
    slack.chat.post_message(channel_name, "아래는 POSTECH 교직원식당 식단입니다.")
    educational_personnel_obj = menu_obj["stores"][4]
    slack.chat.post_message(channel_name, '교직원식당-아침 A-'+educational_personnel_obj["menus"][4]["name"] + ":::" +
                            educational_personnel_obj["menus"][4]["description"])

    # POSTECH 푸드코트
    slack.chat.post_message(channel_name, "아래는 POSTECH 푸드코트 식단입니다.")
    foodcourt_obj = menu_obj["stores"][5]
    slack.chat.post_message(channel_name, '푸드코트-아침(한식)-'+foodcourt_obj["menus"][0]["name"] + ":::" +
                            foodcourt_obj["menus"][0]["description"])
    slack.chat.post_message(channel_name, '푸드코트-중식(한식)-'+foodcourt_obj["menus"][1]["name"] + ":::" +
                            foodcourt_obj["menus"][1]["description"])
    slack.chat.post_message(channel_name, '푸드코트-중식(양식)-'+foodcourt_obj["menus"][2]["name"] + ":::" +
                            foodcourt_obj["menus"][2]["description"])

    # RIST
    slack.chat.post_message(channel_name, "아래는 POSTECH RIST 식단입니다.")
    rist_obj = menu_obj["stores"][6]
    slack.chat.post_message(channel_name, 'RIST-아침-'+rist_obj["menus"][0]["name"] + ":::" +
                            rist_obj["menus"][0]["description"])
    slack.chat.post_message(channel_name, 'RIST-중식-'+rist_obj["menus"][1]["name"] + ":::" +
                            rist_obj["menus"][1]["description"])
    slack.chat.post_message(channel_name, 'RIST-석식-'+rist_obj["menus"][2]["name"] + ":::" +
                            rist_obj["menus"][2]["description"])


def get_menu(boblab_token: str) -> Dict:
    API_HOST = 'https://bablabs.com/openapi/v1/'
    POSTECH_TOKEN = '3hXYy5crHG'
    headers = {'Accesstoken': boblab_token}

    query = {"date": time.strftime("%Y-%m-%d")}
    resp = requests.get(API_HOST + '/campuses/' + POSTECH_TOKEN + '/stores', params=query, headers=headers)
    obj = json.loads(resp.text)
    return obj


def get_rist_menu(browser, menu_obj: Dict) -> Dict:
    browser.get("https://ssgfoodingplus.com/fmn101.do?goTo=todayMenu&storeCd=05600")
    time.sleep(3)
    obj = dict()
    obj["menus"] = dict()
    for idx in range(1, 4):
        login_attempt = browser.find_element_by_xpath('//*[@id="mealType"]/li[' + str(idx) + ']/a')
        login_attempt.click()
        time.sleep(3)

        menu_name = browser.find_element_by_xpath('//*[@id="menuForm"]/section/article/div[4]/div/h6').text
        menu = browser.find_element_by_xpath('//*[@id="menuForm"]/section/article/div[4]/div/ul').text
        iobj = dict()
        iobj["name"] = ":D " + menu_name + "\n"
        iobj["description"] = menu.replace('\n',' ')
        obj["menus"][idx-1] = iobj
    menu_obj["stores"].append(obj)
    return menu_obj


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gets tokens')
    parser.add_argument("slack_token", help="slack token", type=str)
    parser.add_argument("boblab_token", help="boblab token", type=str)
    parser.add_argument("--test", help="if specified, run for test")
    args = parser.parse_args()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    browser = webdriver.Chrome(chrome_options=chrome_options)

    if args.test:
        test = True
        menu_obj = get_menu(args.boblab_token)
        menu_obj = get_postech_menu(menu_obj)
        menu_obj = get_food_court_menu(menu_obj)
        menu_obj = get_rist_menu(browser, menu_obj)
        post_slackbot(args.slack_token, menu_obj, test)
    else:
        while True:
            if time.localtime().tm_hour == 9:
                menu_obj = get_menu(args.boblab_token)
                menu_obj = get_postech_menu(menu_obj)
                menu_obj = get_food_court_menu(menu_obj)
                menu_obj = get_rist_menu(browser, menu_obj)
                post_slackbot(args.slack_token, menu_obj)
            sleep(3600)
