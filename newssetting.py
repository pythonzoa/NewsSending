import json
import requests
from bs4 import BeautifulSoup as bs
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
from datetime import datetime, timedelta
import os
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_settings(settings, filename='settings.json'):
    with open(filename, 'w') as f:
        json.dump(settings, f, indent=4)
    logging.info("설정 파일이 저장되었습니다.")

def load_settings(filename='settings.json'):
    try:
        with open(filename, 'r') as f:
            settings = json.load(f)
        logging.info("설정 파일이 성공적으로 로드되었습니다.")
        return settings
    except FileNotFoundError:
        logging.warning(f"{filename} 파일을 찾을 수 없습니다. 새로운 설정을 입력해주세요.")
        return None

def get_user_input():
    settings = load_settings()
    if settings is None:
        keywords = input("검색할 키워드를 쉼표로 구분하여 입력하세요: ").split(',')
        factors = input("기사 내 반드시 포함될 키워드를 쉼표로 구분하여 입력하세요(or조건): ").split(',')
        title = input("Project명을 입력하세요: ")
        email = input("기사를 받을 사람의 이메일을 쉼표로 구분하여 입력하세요: ").split(',')
        settings = {
            'keywords': keywords,
            'factors': factors,
            'title' : title,
            'email' : email
        }
        save_settings(settings)
    return settings

def extract_article_content(url, keywords):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = bs(response.content, 'html.parser')
        text = ' '.join(soup.stripped_strings)
        return any(keyword in text for keyword in keywords)
    except Exception as e:
        logging.error(f"기사 본문 추출 중 오류: {e}")
        return False

def is_recent_article(date_text):
    now = datetime.now()
    if "분 전" in date_text:
        return True
    elif "시간 전" in date_text or "TOP" in date_text:
        hours_ago = int(re.search(r'\d+', date_text).group())
        article_time = now - timedelta(hours=hours_ago)
        return article_time > now - timedelta(hours=24)
    return False

def get_naver_news(keyword, factors):
    try:
        url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
        response = requests.get(url)
        response.raise_for_status()
        soup = bs(response.text, 'html.parser')
        articles = soup.find_all('div', class_='news_area')
        recent_articles = []
        for article in articles:
            date_infos = article.find_all('span', class_='info')
            article_is_recent = False
            for date_info in date_infos:
                date_text = date_info.text
                if "일 전" in date_text:
                    article_is_recent = False
                    break
                elif is_recent_article(date_text):
                    article_is_recent = True
            if article_is_recent:
                title = article.find('a', class_='news_tit').get('title')
                link = article.find('a', class_='news_tit').get('href')
                if extract_article_content(link, factors):
                    recent_articles.append((title, link))
        return recent_articles
    except Exception as e:
        logging.error(f"네이버 뉴스 검색 중 오류: {e}")
        return []

def send_email(html_content, recipient_emails, title):
    # set SENDER_EMAIL = your_email @ example.com
    # set APP_PASSWORD = your_app_password
    #
    # sender_email = os.getenv("SENDER_EMAIL")
    # app_password = os.getenv("APP_PASSWORD")
    sender_email = "hwijunjang@koreanair.com"
    app_password = "emjb xdrv cweg kbfw"

    if not sender_email or not app_password:
        logging.error("환경 변수에서 이메일 자격증명을 로드하지 못했습니다.")
        return

    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipient_emails)
    msg['Subject'] = f"{title} 최신 뉴스 목록 - {datetime.now().strftime('%y/%m/%d %H:%M')}"
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
            logging.info("이메일이 성공적으로 발송되었습니다.")
    except Exception as e:
        logging.error(f"이메일 전송 실패: {e}")

def generate_email_content(articles):
    if articles:
        html_content = "<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>최신 기사 리스트</title><style>body { font-family: Arial, sans-serif; }.article { margin-bottom: 20px; font-size: 14px; }</style></head><body><h2>최신 기사 리스트</h2>"
        for idx, (title, link) in enumerate(articles, start=1):
            html_content += f'<p class="article">{idx}. <a href="{link}">{title}</a></p>'
        html_content += "</body></html>"
        return html_content
    else:
        return "<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>최신 기사 리스트</title><style>body { font-family: Arial, sans-serif; }.article { margin-bottom: 20px; font_size: 14px; }</style></head><body><h2>최신 기사 리스트</h2><p>새로운 기사가 없습니다.</p></body></html>"

def main():
    settings = get_user_input()
    articles = []
    for keyword in settings['keywords']:
        articles.extend(get_naver_news(keyword, settings['factors']))
    unique_articles = list(set(articles))
    html_content = generate_email_content(unique_articles)
    send_email(html_content, settings['email'], settings['title'])

if __name__ == "__main__":
    main()
