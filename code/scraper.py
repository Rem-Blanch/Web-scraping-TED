# -*- coding: utf-8 -*-
import json
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from random import randint
from time import sleep
from urllib.request import urlopen
from urllib.parse import urljoin
from urllib.error import HTTPError, URLError
from numpy import unique

class firstScraper:
    
    BASE_URL = 'https://www.ted.com/talks'
    FILENAME = 'PRAC_TED_TALK'
    DEFAULT_PAGE_NUMBER = 1

    def __init__(self, language='en'):
        """
        Initialize class.

        @param      String  lang: Language to parse
        """
        self.lang = language                                # Base language.
        self.base_url = firstScraper.BASE_URL               # Default starting url.
        self.page_num = firstScraper.DEFAULT_PAGE_NUMBER    # Default number of pages.
        self.talk_page_list_url = ""                        # URL in search.
        self.talk_page_list = 0                             # Total pages in a talk list.
        self.all_page_list = 0                              # Total links in a page.
        self.all_talk_page_num = 0                          # Total talk pages.
    
    @staticmethod
    def make_request(url):
        """
        Attempts to get the content at `url` by making an HTTP GET request.
        If the content-type of response is some kind of HTML/XML, return the
        text content, otherwise return None.

        @param      string  url: Url to parse
        @return     BeautifulSoup Object
        """
        timeout = 5 
        tries = 0
        while tries <= timeout:
            sleep(randint(3,10))
            try:
                print(url)
                with urlopen(url, timeout=60) as result:
                    if firstScraper.response_handler(result):
                        html = result.read()
            except HTTPError as e:
                print("[DEBUG] in make_request() : Raise HTTPError exception:")
                print("[DEBUG] URL: {} {}".format(url, e))
                tries = tries + 1
            except URLError as e:
                print("[DEBUG] in make_request() : Raise URLError exception:")
                print("[ERROR] ", e)
                tries = tries + 1
            else:
                print("[DEBUG] in make_request() : It Worked!")
                return BeautifulSoup(html, 'html.parser')
    
    @staticmethod
    def response_handler(resp):
        """
        Returns True if the response seems to be HTML, False otherwise.

        @param      string  resp: Respones to evaluate
        @return     boolean 
        """
        content_type = resp.headers['Content-Type'].lower()
        return (resp.getcode() == 200 
                and content_type is not None 
                and content_type.find('html') > -1)

    def find_next_pagination(self, soup):
        """
        Retrive link for the next talk page.
        @param      BeautifulSoup  - soup: Data to parse.
        @return     String         - next_page_href: Next page link.
        """
        pages = soup.find('div', {'role': 'navigation', 'class': 'pagination'})
        next_page_href = urljoin(self.base_url, pages.find("a", {"class", "pagination__next"}).attrs['href'])
        
        if next_page_href is None:
            return None
        
        return next_page_href

    def get_pagination(self):
        """
        Retrive link for the next talk page.
        @param      Integer        - num_pages: Number of pages to try to retrieve.
        @return     List           - page_list: List of links.
        """
        page_url = firstScraper.BASE_URL
        page_list = []
        page_list.append(page_url)
        pages = 0
        while pages < self.page_num:
            
            talk_soup = firstScraper.make_request(page_url)
            next_page = self.find_next_pagination(talk_soup)

            if next_page is None:
                break
            
            page_url = next_page
            page_list.append(next_page)
            pages += 1
            print("[DEBUG] Actual page: {} from {}".format(pages, self.page_num))
            
        return page_list

    def find_talk_title(self, soup):
            """
            Get talk title.

            @param      BeautifulSoup  - soup: data to parse
            @return     String         - title: Title
            """
            return soup.find("h4", {'class': 'h9'}).find('a').get_text().strip()

    def find_talk_link(self, soup):
        """
        Get talk link

        @param      BeautifulSoup  - soup: data to parse
        @return     String         - link: Link
        """
        return soup.find('h4', {'class': 'h9'}).find('a').attrs['href']

    def find_talk_speaker(self, soup):
        """
        Get talk link

        @param      BeautifulSoup  - soup: data to parse
        @return     String         - link: Link
        """
        return soup.find('h4', {'class': 'h12'}).get_text().strip()

    def find_talk_posted_date(self, soup):
        """
        Get talk upload date

        @param      BeautifulSoup  - soup: data to parse
        @return     String         - link: Link
        """
        return soup.find('div', {'class': 'meta'}).find('span', {'class': 'meta__val'}).get_text().strip()

    def get_talk_titles(self, soup):
        """
        Obtain all talk titles from the actual page.

        @param      BeautifulSoup - soup : Data to parse
        @return     List          - titles  : List of titles
        """
        titles = soup.find_all('div', {'class': 'talk-link'})
        titles = [self.find_talk_title(text) for text in titles]

        return titles

    def get_talk_links(self, soup):
        """
        Get a link from each talk in our current page.

        @param      BeautifulSoup  - soup  : Data to parse
        @return     String         - links : Parsed information
        """
        unrefined_links = soup.find_all('div', {'class': 'talk-link'})
        talk_links = [self.find_talk_link(text) for text in unrefined_links]
        talk_links = [urljoin(self.base_url, link) for link in talk_links]
        return talk_links

    def get_talk_speakers(self, soup):
        """
        Get speakers from each talk in our current page.

        @param      BeautifulSoup  - soup  : Data to parse
        @return     String         - links : Parsed information
        """
        m_speakers = soup.find_all('div', {'class': 'talk-link'})
        m_speakers = [self.find_talk_speaker(text) for text in m_speakers]

        return m_speakers

    def get_talk_posted_date(self, soup):
        """
        Get upload date from each talk in our current page.

        @param      BeautifulSoup  - soup  : Data to parse
        @return     String         - links : Parsed information
        """
        posted_dates = soup.find_all('div', {'class': 'talk-link'})
        posted_dates = [self.find_talk_posted_date(text) for text in posted_dates]

        datetime_posted = [self.normalize_date(dates) for dates in posted_dates] 
        return datetime_posted

    def find_talk_information(self, soup):
        """
        Get header to scrap.

        @param      BeautifulSoup  - soup  : Data to parse
        @return     BeautifulSoup  - talk_head : Fragment to parse
        """       
        talk_head = soup.find("head")
        return talk_head

    def find_talk_tags(self, talk_head):
        """
        Get tags from current talk.

        @param      BeautifulSoup  - talk_head  : Data to parse
        @return     String         - links : Parsed information
        """
        talk_tags = talk_head.find_all("meta", property='og:video:tag')
        return  [tags.attrs['content'] for tags in talk_tags]

    def find_talk_title_description(self, soup):
        """
        Find the talk title and description from talk page.
        
        @param      BeautifulSoup  - soup  : Data to parse
        @return     String         - talk_title, talk_description : Parsed information
        """
        talk_title = soup.find('meta', property='og:title').attrs['content']
        talk_description = soup.find('meta', property='og:description').attrs['content']
        return talk_title, talk_description

    def find_talk_duration(self, soup):
        """
        Find the duration from talk page.
        
        @param      BeautifulSoup  - soup  : Data to parse
        @return     String         - talk_duration : Parsed information
        """
        talk_duration = soup.find("meta", property='og:video:duration').attrs['content']
        return self.seconds_to_minute(talk_duration)

    def find_talk_upload_date(self, soup):
        """
        Find the upload date from talk page.
        
        @param      BeautifulSoup  - soup  : Data to parse
        @return     String         - talk_upload_date : Parsed information
        """
        talk_upload_date = soup.find("meta", property='og:video:release_date').attrs['content']
        return self.seconds_to_date(talk_upload_date)

    def find_talk_views(self, soup):
        """
        Find the talk title and description from talk page
        @param      BeautifulSoup  - soup  : Data to parse
        @return     String         - talk_title, talk_description : Parsed information
        """
        talk_div = soup.find("div", {"class", "main talks-main"})
        talk_views = talk_div.find("meta", itemprop="interactionCount").attrs['content']
        return talk_views

    def find_talk_authors(self, soup):
        talk_div = soup.find("div", {"class", "main talks-main"})
        talk_authors = talk_div.find_all("span", itemprop='author')
        return [self.get_talk_authors(author) for author in talk_authors]    

    def get_talk_authors(self, soup):
        """
        Find speakers from talk page.
        
        @param      BeautifulSoup  - soup  : Data to parse
        @return     String         - author_name, author_link : Parsed information
        """
        author_name = soup.find('meta', itemprop='name').attrs['content']
        author_link = soup.find('link', itemprop='url').attrs['href']
        return author_name, urljoin(self.base_url, author_link)

    def get_talk_languages(self, soup):
        try:
            tl_soup = soup.find("script", {'data-spec': "q"}).string
            regex = r"(?<=languageName\"\:\")\w+"
            matches = re.finditer(regex, tl_soup, re.MULTILINE)
            languageName = []

            for match in matches:
                languageName.append(match.group())
            languageName = [i for i in languageName if i]
            
            languages = unique(languageName).tolist()
            return languages
        except AttributeError as e:
            print("[DEBUG] in get_talk_languages() : Raise URLError exception:", e)
            return None
       
    def get_talk_transcript_url(self, t_link):
        transcript_dash = '/transcript'
        transcript_url = t_link + transcript_dash
        return transcript_url

    def get_talk_transcript(self, soup):
        talk_text = soup.find_all("div", {"class": "Grid__cell flx-s:1 p-r:4"})
        text = []
        text = [pharagraph.find('p').text for pharagraph in talk_text]
        return [self.normalize_text(x) for x in text]


    def talk_detail_information(self, page_url):
        """
        Get detailed information from all talks from one talk page.
        Creates a JSON file with the extracted information.
        Stores it in a file.
        
        @param      String      - page_url  : Url to scrap.
        """
        talk_soup = self.make_request(page_url)
        
        print("[GET] get talk posted date ...")
        talk_date = self.get_talk_posted_date(talk_soup)
        print("[GET] get talk titles ...")
        talk_titles = self.get_talk_titles(talk_soup)
        print("[GET] get talk links ...")
        talk_links = self.get_talk_links(talk_soup)
        print("[GET] get talk speakers ...")
        talk_speakers = self.get_talk_speakers(talk_soup)
        print("[GET] get talk language ...")
        talk_lang = self.lang

        talk_topics = []
        talk_authors = []
        talk_languages = []
        talk_transcript = []

        talk_num = len(talk_links)
        self.all_page_list = talk_num

        print("[GET] get talk topics and transcripts ...")
        for i, link in enumerate(talk_links):
            self.target_page_num = i + 1
            self.target_url = link
            print("  [{}/{}] Target URL: {}".format(i + 1, talk_num, link))
            ta_soup = firstScraper.make_request(link)
            update_date = self.get_scrape_date()
            print("[GET] get talk title & description")
            talk_title, talk_description = self.find_talk_title_description(ta_soup)
            print("[GET] get talk topics")
            talk_topics.append(self.find_talk_tags(ta_soup))
            print("[GET] get talk duration")
            talk_duration = self.find_talk_duration(ta_soup)
            print("[GET] get talk upload date")
            talk_upload_date = self.find_talk_upload_date(ta_soup)
            print("[GET] get talk views")
            talk_views = self.find_talk_views(ta_soup)
            print("[GET] get talk authors")
            talk_authors.append(self.find_talk_authors(ta_soup))
            print("[GET] get talk languages")
            talk_languages.append(self.get_talk_languages(ta_soup))
            print("[GET] get transcript")
            transcript_url =  self.get_talk_transcript_url(link)
            transcript_soup = firstScraper.make_request(transcript_url)
            if transcript_soup is not None:
                talk_transcript.append(self.get_talk_transcript(transcript_soup))
        
        print("[OPEN] open json file ...")
        json_file = open(self.FILENAME, "w")

        print("[CREATE] creating talk JSON data ...")
        for date, title, link, speakers, authors, topics, talk_languages, talk_transcript in zip(talk_date, talk_titles, talk_links, talk_speakers, talk_authors, talk_topics, talk_languages, talk_transcript):

            talk_data = {
                "posted_date": date,
                "update_date": update_date,
                "talk_title": title,
                "talk_description": talk_description,
                "talk_main_speaker": speakers,
                "talk_speakers_info": authors,
                "talk_link": link,
                "talk_lang": talk_lang,
                "available_languages": talk_languages,
                "talk_topics": topics,
                "talk_duration": talk_duration,
                "talk_transcript": talk_transcript,
                "talk_upload_video_date": talk_upload_date,
                "talk_views": talk_views,

            }
        
            print("[INSERT] insert JSON data: {} ...", title)
            json.dump(talk_data, json_file, indent=2)

    def talk_all_information(self, page_list = None):
        """
        Get detailed information from an specific number of talk pages.
        
        @param      String      - page_list  : Urls to scrap.
        """
        try:
            if page_list is None:
                page_list = self.get_pagination()
            
            page_num = len(page_list)
            self.all_talk_page_num = page_num

            for i, page in enumerate(page_list):
                self.talk_page_list_url = page
                self.talk_page_list = i + 1
                self.talk_detail_information(page)
        except:
            print("[DEBUG] Raise except:")
            print("[DEBUG] Target page list url: {}".format(self.talk_page_list_url))
            print("[DEBUG] Target URL: {}".format(self.base_url))


####################################

    def seconds_to_minute(self, timer):
        return str(timedelta(seconds=float(timer)))

    def seconds_to_date(self, date):
        return str(datetime.utcfromtimestamp(0) + timedelta(seconds=float(date)))

    def normalize_date(self, date):
        norm_date = datetime.strptime(date, '%b %Y')
        norm_date = norm_date.strftime("%d-%b-%Y")
        return norm_date
    
    def normalize_text(self, text):
        rep = {"\t": "", "\n": " "}
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)
        return text

    def get_scrape_date(self):
        """
        Return the date on which scraping was performed

        @return     String         - links : Date of scraping process.
        """
        today = date.today()
        return str(today.strftime('%Y-%m-%d'))          
        