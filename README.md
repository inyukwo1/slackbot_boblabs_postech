# slackbot_boblabs_postech

* 실행 방법: python main.py "slack token" "bablab token" [--test True] (token은 나인혁에게 문의하여 받는다.)

installation guide
1. pip install --upgrade google-cloud-storage
2. pip install -r requirements.txt
3. brew install chromedriver
4. export GOOGLE_APPLICATION_CREDENTIALS="./postech-dblab-slackbot-05fa2b0665fc.json" (파일은 나인혁에게 받는다.)


규칙
1. 일주일에 한 시간 이상씩 각자 contribution한다. (어떤 contribution을 해야 하는지는 github issue에 등록)
2. 소스 코드는 마스터가 아닌 각자 다른 브랜치를 만들어 수정하고, 마스터에 반영해야 될 때 pull request를 날려 검토를 받은 뒤 마스터 브랜치에 적용될 수 있도록
한다.
3. "#밥" 채널은 공식적으로 사용하는 것으로 하고, 테스트는 private 채널을 따로 파서 사용한다.
