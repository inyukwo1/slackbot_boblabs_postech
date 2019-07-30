from slacker import Slacker
from typing import Dict, Tuple, List
import requests
import argparse
import time
from time import sleep
import json, io, os
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from google.cloud import vision
from google.cloud.vision import types
from PIL import Image


def get_postech_menu() -> List:
    url = 'http://fd.postech.ac.kr/bbs/today_menu.php?bo_table=weekly'
    html = requests.get(url)
    html.encoding='utf-8'
    html = html.text
    soup = BeautifulSoup(html, 'lxml')
    tags = soup.find_all('td', class_='txtheight')
    obj = []
    name_list = ["조식A", "조식B", "중식", "석식", "교직원"]
    for idx, tag in enumerate(tags):
        description = tag.get_text().encode('utf-8','strict')
        description = description.decode('utf-8','strict')
        iobj = dict()
        iobj["name"] = name_list[idx]
        description = description.replace('\n',' ').replace('\r', ' ').replace('&',' ')
        description = re.sub('[a-zA-z]*', '', description).replace('"', '')
        description = re.sub('[\s]+', ' ', description)
        iobj["description"] = description
        obj.append(iobj)
    return obj


def get_food_court_menu() -> List:
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
    j, obj = 0, []
    for i in [8, 12, 13]:
        description = contents[i].get_text().replace('+',' ').replace('-',' ').replace('\n',' ').replace('\r', ' ').replace('&',' ')
        description = re.sub('[a-zA-z]*', '', description).replace('"', '')
        description = re.sub('[\s]+', ' ', description)
        iobj = dict()
        iobj["name"] = ""
        iobj["description"] = description
        obj.append(iobj)
    return obj


def ocr_gasokgi_menu(jpg_path: str) -> Tuple[str, str]:
    weekday = time.localtime().tm_wday
    if weekday == 5 or weekday == 6:
        return "토, 일요일에는 점심을 제공하지 않습니다.", "토, 일요일에는 저녁을 제공하지 않습니다."

    origin_img = Image.open(jpg_path)
    double_lunch = False
    if origin_img.width > 1300:
        if weekday < 2:
            left = 75 + 200 * weekday
            lunch_top = 150
            dinner_top = 485
            lunch_box_width = 200
            dinner_box_width = 200
            box_height = 300
        elif weekday > 2:
            left = 75 + 200 * (weekday + 1)
            lunch_top = 150
            dinner_top = 485
            lunch_box_width = 200
            dinner_box_width = 200
            box_height = 300
        else:
            left = 475
            lunch2_left = 675
            lunch_top = 150
            dinner_top = 485
            lunch_box_width = 200
            dinner_box_width = 400
            box_height = 300
            double_lunch = True
    else:
        left = 75 + 200 * weekday
        lunch_top = 150
        dinner_top = 485
        lunch_box_width = 200
        dinner_box_width = 200
        box_height = 300

    lunch_img = origin_img.crop((left, lunch_top, left + lunch_box_width, lunch_top + box_height))
    lunch_img.save("lunch_img.jpg")
    dinner_img = origin_img.crop((left, dinner_top, left + dinner_box_width, dinner_top + box_height))
    dinner_img.save("dinner_img.jpg")

    with open('lunch_img.jpg', 'rb') as image_file:
        lunch_content = image_file.read()
    with open('dinner_img.jpg', 'rb') as image_file:
        dinner_content = image_file.read()
    lunch_cloud_img = types.Image(content=lunch_content)
    dinner_cloud_img = types.Image(content=dinner_content)
    client = vision.ImageAnnotatorClient()

    lunch_response = client.text_detection(image=lunch_cloud_img)
    lunch_label = lunch_response.text_annotations[0].description.replace("\n", ", ")
    dinner_response = client.text_detection(image=dinner_cloud_img)
    dinner_label = dinner_response.text_annotations[0].description.replace("\n", ", ")

    if double_lunch:
        lunch_img2 = origin_img.crop((lunch2_left, lunch_top, lunch2_left + lunch_box_width, lunch_top + box_height))
        lunch_img2.save("lunch_img2.jpg")
        with open('lunch_img2.jpg', 'rb') as image_file:
            lunch_content = image_file.read()
        lunch2_cloud_img = types.Image(content=lunch_content)
        lunch2_response = client.text_detection(image=lunch2_cloud_img)
        lunch2_label = lunch2_response.text_annotations[0].description.replace("\n", ", ")
        lunch_label += "//menu B: " + lunch2_label

    return lunch_label, dinner_label


def post_slackbot(slack_token: str, inje_menu, gasok_menu, postech_menu, foodcourt_menu, rist_menu, test: bool=False) -> None:
    slack = Slacker(slack_token)
    channel_name = "#밥_dev" if test else "#밥"

    slack.chat.post_message(channel_name, '★오늘의 식단을 소개합니다★')

    # 인재개발원
    for menu in inje_menu:
        slack.chat.post_message(channel_name, '♥인재개발원♥-'+menu["name"] + ":::" + menu["description"])

    # 가속기
    for menu in gasok_menu:
        slack.chat.post_message(channel_name, '♥가속기♥-'+menu["name"] + ":::" + menu["description"])

    for menu in postech_menu:
        slack.chat.post_message(channel_name, '♥학생식당♥-'+menu["name"] + ":::" + menu["description"])

    # POSTECH 푸드코트
    for menu in foodcourt_menu:
        slack.chat.post_message(channel_name, '♥푸드코트♥-'+menu["name"] + ":::" + menu["description"])

    # RIST
    for menu in rist_menu:
        slack.chat.post_message(channel_name, '♥RIST♥-'+menu["name"] + ":::" + menu["description"])

def get_rist_menu(browser) -> List:
    browser.get("https://ssgfoodingplus.com/fmn101.do?goTo=todayMenu&storeCd=05600")
    time.sleep(3)
    obj = []
    for idx in range(1, 4):
        login_attempt = browser.find_element_by_xpath('//*[@id="mealType"]/li[' + str(idx) + ']/a')
        login_attempt.click()
        time.sleep(3)

        menu_name = browser.find_element_by_xpath('//*[@id="menuForm"]/section/article/div[4]/div/h6').text
        menu = browser.find_element_by_xpath('//*[@id="menuForm"]/section/article/div[4]/div/ul').text
        iobj = dict()
        iobj["name"] = ":D " + menu_name + "\n"
        iobj["description"] = menu.replace('\n',' ')
        obj.append(iobj)
    return obj


def get_inje_menu(browser):
    browser.get("https://www.poswel.co.kr/fmenu/three_days.php?area_code=A4&amp")
    time.sleep(3)
    obj = []
    menu_name = browser.find_element_by_xpath('//*[@id="list_3day"]/div[1]/div[2]/div/div[1]/div[2]/strong').text
    menu = browser.find_element_by_xpath('//*[@id="list_3day"]/div[1]/div[2]/div/div[2]/span[1]').text
    iobj = dict()
    iobj["name"] = ":D " + menu_name + "\n"
    iobj["description"] = menu.replace('\n',' ')
    obj.append(iobj)

    menu_name = browser.find_element_by_xpath('//*[@id="list_3day"]/div[1]/div[3]/div/div[1]/div[2]/strong').text
    menu = browser.find_element_by_xpath('//*[@id="list_3day"]/div[1]/div[3]/div/div[2]/span[1]').text
    iobj = dict()
    iobj["name"] = ":D " + menu_name + "\n"
    iobj["description"] = menu.replace('\n',' ')
    obj.append(iobj)

    menu_name = browser.find_element_by_xpath('//*[@id="list_3day"]/div[1]/div[4]/div/div[1]/div[2]/strong').text
    menu = browser.find_element_by_xpath('//*[@id="list_3day"]/div[1]/div[4]/div/div[2]/span[1]').text
    iobj = dict()
    iobj["name"] = ":D " + menu_name + "\n"
    iobj["description"] = menu.replace('\n',' ')
    obj.append(iobj)


    menu_name = browser.find_element_by_xpath('//*[@id="list_3day"]/div[1]/div[5]/div/div[1]/div[2]/strong').text
    menu = browser.find_element_by_xpath('//*[@id="list_3day"]/div[1]/div[5]/div/div[2]/span[1]').text
    iobj = dict()
    iobj["name"] = ":D " + menu_name + "\n"
    iobj["description"] = menu.replace('\n',' ')
    obj.append(iobj)

    return obj


def get_gasok_menu(browser):
    browser.get("https://bds.bablabs.com/restaurants?campus_id=3hXYy5crHG")
    time.sleep(3)
    obj = []
    menu_img = browser.find_element_by_xpath('//*[@id="app"]/div[1]/div/div/div/div[6]/div[2]/div/div/div/div[2]/div[2]/div/img').get_attribute('src')

    tmp_file_loc = "tmp.jpg"
    with open(tmp_file_loc, 'wb') as f:
        resp = requests.get(menu_img, verify=False)
        f.write(resp.content)
    lunch, dinner = ocr_gasokgi_menu(tmp_file_loc)
    obj.append({"name": "점심",
                "description": lunch})
    obj.append({"name": "저녁",
                "description": dinner})

    return obj


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gets tokens')
    parser.add_argument("slack_token", help="slack token", type=str)
    parser.add_argument("--test", help="if specified, run for test")
    args = parser.parse_args()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    browser = webdriver.Chrome(chrome_options=chrome_options)

    if args.test:
        test = True
        inje_menu = get_inje_menu(browser)
        gasok_menu = get_gasok_menu(browser)
        postech_menu = get_postech_menu()
        foodcourt_menu = get_food_court_menu()
        rist_menu = get_rist_menu(browser)
        post_slackbot(args.slack_token, inje_menu, gasok_menu, postech_menu, foodcourt_menu, rist_menu, test)
    else:
        while True:
            if time.localtime().tm_hour == 9:
                inje_menu = get_inje_menu(browser)
                gasok_menu = get_gasok_menu(browser)
                postech_menu = get_postech_menu()
                foodcourt_menu = get_food_court_menu()
                rist_menu = get_rist_menu(browser)
                post_slackbot(args.slack_token, inje_menu, gasok_menu, postech_menu, foodcourt_menu, rist_menu)
            sleep(3600)
