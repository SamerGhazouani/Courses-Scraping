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
    base_url = f"https://alison.com/courses?query={query}"
    page_number = 1
    course_links = []

    while True:
        url = f"{base_url}&page={page_number}"
        driver.get(url)
        time.sleep(3)
        # If there are no results for the search made, we break from the loop
        if driver.find_element(By.CSS_SELECTOR, 'div.no-results').get_attribute('style'):
            break
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'search-heading')))

        soup = BeautifulSoup(driver.page_source, 'lxml')
        course_elements = soup.select('a.card__more.card__more--mobile')

        for course_element in course_elements:
            link = course_element.get('href')
            if link:
                course_links.append(link)

        # Check for the next page link
        next_button = soup.select_one('span.current.next')
        if next_button:
            break
        else:
            page_number += 1

    return course_links

def scrape_alison_courses(query):
    driver = webdriver.Chrome()
    courses = []
    course_links = get_links(driver, query)
    if len(course_links) == 0:
        print('No courses found in Alison')
        return courses
    try:
        # After we get all the links we navigate to them one by one and extract the data needed
        for course_link in course_links:
            driver.get(course_link)
            time.sleep(3)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.landing__content')))
            except:
                print(f"Error loading course link: '{course_link}'")
                continue

            course_soup = BeautifulSoup(driver.page_source, 'lxml')
            title = course_soup.select_one('h1.course-title').get_text(strip=True).replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if course_soup.select_one('h1.course-title') else 'Title not found'
            # The description is not always found so we initiate it as not found then look for it
            description = 'Description not found'
            if course_soup.select_one('div.l-desc.course-desc'):
                description_element = course_soup.select_one('div.l-desc.course-desc')
                paragraphs = description_element.select('p')
                description = '\n'.join([paragraph.get_text(strip=True) for paragraph in paragraphs]) if paragraphs else 'Description not found'
            instructor = course_soup.select_one('span.course-publisher.l-pub__name').get_text(strip=True) if course_soup.select_one('span.course-publisher.l-pub__name') else 'Alison Staff'
            duration = f"{course_soup.select_one('span.course-avg_duration.l-time').get_text(strip=True)} Hours" if course_soup.select_one('span.course-avg_duration.l-time') else 'Duration not found'
            # Unfortunately there is no element showing the level of the course, so we set it as not found
            level = 'Level not found'
            # The skills aren't always present, so we initiate it as the query we're searching for then check the element having it
            skills = f'{query}'
            information_elements = course_soup.select('div.l-section__inner')
            if information_elements:
                for information_element in information_elements:
                    information_name = information_element.select_one('h3')
                    if information_name and information_name.get_text(strip=True) == 'Knowledge & Skills You Will Learn':
                        skills_list = information_element.select('a')
                        skills = ','.join([skill.get_text(strip=True) for skill in skills_list]) if skills_list else f'{query}'
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
            # The best thing about this site that all the courses are free
            price = 'Free'
            # For the image we have 2 options, either getting the image associated with the course or the thumbnail of the video associated with the course
            img_element = course_soup.select_one('div.l-card__img > img')
            if img_element:
                img_link = img_element.get('src')
            else:
                img_link = 'Image not found'
            if img_link == 'Image not found':
                img_element = course_soup.select_one('img.video-container__bg')
                if img_element:
                    img_link = img_element.get('src')
                else:
                    img_link = 'Image not found'

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

        print(f"Courses from Alison: {len(courses)}")
        return courses

    except Exception as e:
        print(f"Error scraping course link '{course_link}' :")
        print(e)
        print(f"Courses from Alison: {len(courses)}")
        return courses

    finally:
        driver.quit()