from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from langdetect import detect, LangDetectException
import langcodes

# This function will allow us to navigate through all the pages and get all the courses's links
def get_links(driver, query):
    base_url = f"https://www.udacity.com/catalog/all/any-price/any-school/any-skill/any-difficulty/any-duration/any-type/relevance/page-1?searchValue={query}"
    page_number = 1
    course_links = []

    while True:
        url = base_url.replace('page-1', f'page-{page_number}')
        driver.get(url)
        time.sleep(3)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.css-15y92lb')))

        soup = BeautifulSoup(driver.page_source, 'lxml')
        course_elements = soup.select('a.chakra-heading.css-1rsglaw')
        for course_element in course_elements:
            link = course_element.get('href')
            if link:
                course_links.append(f"https://www.udacity.com{link}")

        # Check for the next page link
        next_button = soup.select_one('button.chakra-button.css-6d1oup')
        if next_button and not next_button.has_attr('disabled'):
            page_number += 1
        else:
            break

    return course_links

def scrape_udacity_courses(query):
    driver = webdriver.Chrome()
    courses = []
    course_links = get_links(driver, query)
    # If there are no results for the search made, we return an empty list
    if len(course_links) == 0:
        print('No courses found in Udacity')
        return courses

    try:
        # After we get all the links we navigate to them one by one and extract the data needed
        for course_link in course_links:
            driver.get(course_link)
            time.sleep(3)
            # Sometimes the search results contain a link that's not valid anymore, so we need to check for that first
            if driver.find_elements(By.CSS_SELECTOR, 'div.css-12h0olz'):
                continue
            time.sleep(3)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.css-13a007i')))
            except:
                print(f"Error loading course link: '{course_link}'")
                continue

            course_soup = BeautifulSoup(driver.page_source, 'lxml')
            title = course_soup.select_one('h1.chakra-heading.css-vl0zfv').get_text(strip=True).replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if course_soup.select_one('h1.chakra-heading.css-vl0zfv') else 'Title not found'
            description = course_soup.select_one('p.chakra-text.css-8kqdt8').get_text(strip=True) if course_soup.select_one('p.chakra-text.css-8kqdt8') else 'Description not found'
            # A course may have more than one instructor, so we join them together
            instructor_elements = course_soup.select('h3.chakra-heading.css-1hsf0v9')
            instructor = ','.join([element.get_text(strip=True) for element in instructor_elements]) if instructor_elements else 'Udacity Staff'
            # The duration and level are both stored in the same element, so we look for them using some keywords
            duration = 'Duration not found'
            level = 'Level not found'
            information_elements = course_soup.select('div.css-135ny1a')
            for information_element in information_elements:
                information = information_element.select_one('p.chakra-text.css-1vs1lpm').get_text(strip=True)
                if any(keyword in information for keyword in ["Beginner", "Intermediate", "Advanced"]):
                    level = information
                elif any(keyword in information for keyword in ["day", "days", "week", "weeks", "month", "months", "hour", "hours", "minute", "minutes"]):
                    duration = information
            # We locate the element containing the skills and replace ' • ' with ',' so that all the skills have the same format in the database
            skills = f'{query}'
            if course_soup.select_one('figure.css-amj7dw > div.css-0'):
                if course_soup.select_one('figure.css-amj7dw > div.css-0').get_text(strip=True).find('+')!=-1:
                    skills = course_soup.select_one('figure.css-amj7dw > div.css-0').get_text(strip=True)[:course_soup.select_one('figure.css-amj7dw > div.css-0').get_text(strip=True).find('+')].replace(' • ', ',').strip()
                else:
                    skills = course_soup.select_one('figure.css-amj7dw > div.css-0').get_text(strip=True).replace(' • ', ',').strip()
            # We don't have any information about the language of the course so we detect it automatically through the description and if it's not found we use the title
            try:
                if description != 'Description not found':
                    code = detect(description)
                    language = langcodes.Language.get(code).display_name()
                else:
                    code = detect(title)
                    language = langcodes.Language.get(code).display_name()
            except LangDetectException:
                language = 'Language not found'
            # The price isn't always shown, but when it's free a sticker appear so we initiate it as 'Paid' and to look for that sticker
            price = 'Paid'
            if course_soup.select_one('span.chakra-badge.css-voosbm'):
                if course_soup.select_one('span.chakra-badge.css-voosbm').get_text(strip=True) == 'Free':
                    price = 'Free'
            # For the image, we detect its location than extract the src
            img_link = 'Image not found'
            if course_soup.select_one('div.css-1xzc08i'):
                img_element = course_soup.select_one('div.css-1xzc08i')
                if img_element.select_one('img'):
                    img_link = img_element.select_one('img').get('src')

            courses.append({
                'title': title,
                'description': description,
                'instructor': instructor,
                'duration': duration,
                'skills': skills,
                'level': level,
                'language': language,
                'price': price,
                'img_link': img_link,
                'course_link': course_link,
            })

        print(f"Courses from Udacity: {len(courses)}")
        return courses

    except Exception as e:
        print(f"Error scraping course link '{course_link}' :")
        print(e)
        print(f"Courses from Udacity: {len(courses)}")
        return courses

    finally:
        driver.quit()