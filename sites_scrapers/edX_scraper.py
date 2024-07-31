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
    base_url = f"https://www.edx.org/search?q={query}&tab=course"
    page_number = 1
    course_links = []

    while True:
        url = f"{base_url}&page={page_number}"
        driver.get(url)
        time.sleep(8)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.card-container')))
        # If there are no results for the search made, we break from the loop
        if driver.find_elements(By.CSS_SELECTOR, 'div.alert-dialog'):
            break

        soup = BeautifulSoup(driver.page_source, 'lxml')
        # There are two types of elements, so we select them both
        course_elements = soup.select('a.base-card-link, a.expanded-product-card-link')
        for course_element in course_elements:
            course_links.append(f"https://www.edx.org{course_element['href']}")

        next_button = soup.select_one('button.next')
        if next_button and not next_button.has_attr('disabled'):
            page_number += 1
        else:
            break

    return course_links

def scrape_edx_courses(query):
    driver = webdriver.Chrome()
    courses = []
    course_links = get_links(driver, query)
    if len(course_links) == 0:
        print('No courses found in edX')
        return courses

    try:
        # After we get all the links we navigate to them one by one and extract the data needed
        for course_link in course_links:
            driver.get(course_link)
            time.sleep(3)
            # Sometimes the search results contain a link that's not valid anymore, so we need to check for that first
            if driver.find_elements(By.CSS_SELECTOR, 'div.school-details'):
                continue
            if driver.find_elements(By.CSS_SELECTOR, 'div.error-code.pt-2'):
                continue
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'main-content')))
            except:
                print(f"Error loading course link: '{course_link}'")
                continue
            course_soup = BeautifulSoup(driver.page_source, 'lxml')
            # The title element has the format of "Institution: Title" so we get only the second part
            title = 'Title not found'
            if course_soup.select_one('div.col-md-7.pr-4'):
                title_element = course_soup.select_one('div.col-md-7.pr-4')
                title = title_element.select_one('h1').get_text(strip=True)[title_element.select_one('h1').get_text(strip=True).find(': ')+2:].replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if title_element.select_one('h1') else 'Title not found'
            if title == 'Title not found' and course_soup.select_one('div.col-md-7'):
                title_element = course_soup.select_one('div.col-md-7')
                title = title_element.select_one('h1').get_text(strip=True)[title_element.select_one('h1').get_text(strip=True).find(': ')+2:].replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if title_element.select_one('h1') else 'Title not found'
            # The description isn't always available, so we initiate it as not found then we start looking for it
            description = 'Description not found'
            if course_soup.select('div.mt-2.lead-sm.html-data'):
                description_element = course_soup.select_one('div.mt-2.lead-sm.html-data')
                paragraphs = description_element.select('p')
                # The element containing the description may sometimes have multiple paragraphs or doesn't have any, so we check both cases
                if paragraphs:
                    description = '\n'.join([p.get_text(strip=True) for p in paragraphs])
                elif course_soup.select_one('div.mt-2.lead-sm.html-data').getText(strip=True):
                    description = course_soup.select_one('div.mt-2.lead-sm.html-data').getText(strip=True)
            #The instructor, level, language and skills are found in the same element, so we extract them using the name of each piece of information given
            instructor = 'edX Staff'
            level = 'Level not found'
            language = 'Language not found'
            skills = f'{query}'
            if course_soup.select('ul.mb-0.pl-3.ml-1') :
                left_informations_list = course_soup.select('ul.mb-0.pl-3.ml-1')[0]
                left_informations = left_informations_list.select('li')
                for information in left_informations:
                    if information.select('span.font-weight-bold'):
                        information_name = information.select_one('span.font-weight-bold').get_text(strip=True)
                        if information_name == "Institution:":
                            instructor = information.get_text(strip=True).replace("Institution:", "").strip()
                        elif information_name == "Institutions:":
                            instructor = information.get_text(strip=True).replace("Institutions:", "").strip()
                        elif information_name == "Level:":
                            level = information.get_text(strip=True).replace("Level:", "").strip()
                        elif information_name == "Language:":
                            language = information.get_text(strip=True).replace("Language:", "").strip()
                right_informations_list = course_soup.select('ul.mb-0.pl-3.ml-1')[1]
                right_informations = right_informations_list.select('li')
                for information in right_informations:
                    if information.select('span.font-weight-bold'):
                        information_name = information.select_one('span.font-weight-bold').get_text(strip=True)
                        if information_name == "Associated skills:":
                            skills = information.select('span')[1].get_text(strip=True).replace(', ', ',')
                        elif information_name == "Language:":
                            language = information.get_text(strip=True).replace("Language:", "").strip()
            # If we still didn't locate the language, we may try to detect it automatically
            # We detect it automatically through the description and if it's not found we use the title
            try:
                if description != 'Description not found':
                    code = detect(description)
                    language = langcodes.Language.get(code).display_name()
                else:
                    code = detect(title)
                    language = langcodes.Language.get(code).display_name()
            except LangDetectException:
                language = 'Language not found'
            # The price isn't always shown so we initiate it as not found and to look for it we have 3 options
            price = 'Price not found'
            # Option 1: We locate the element that gives us the information if the course is free or not
            if course_soup.select('.course-snapshot-content .row .col-md-4'):
                price_element = course_soup.select('.course-snapshot-content .row .col-md-4')
                for price_value in price_element:
                    price_information = price_value.select_one('div.small')
                    if price_information:
                        if price_information.get_text(strip=True) == 'Access to course at no cost':
                            price = 'Free'
                        else:
                            price = 'Paid'
            # Option 2: If the first element is not found we search for a table that tells us if the course gives us a paid certificate or not
            if price == 'Price not found' and course_soup.select_one('.track-comparison-table'):
                price='Paid'
            # Option 3: If the price is still not found we look if we can access the course materials or not
            if price == 'Price not found' and course_soup.select_one('div.main-enroll-btn'):
                if course_soup.select_one('div.main-enroll-btn').get_text(strip=True)=='View course materials':
                    price = 'Free'
            duration = 'Duration not found'
            if course_soup.select_one('.course-snapshot-content .row .col-md-4:nth-child(1)'):
                duration_element = course_soup.select_one('.course-snapshot-content .row .col-md-4:nth-child(1)')
                duration = duration_element.select_one('div.h4.mb-0').get_text(strip=True)
            img_link = 'Image not found'
            # For the image link we can find it either as an image and take the link or or we can find it as a video and take the thumbnail link
            if course_soup.select_one('.CloudflareImage.header-image'):
                img_element = course_soup.select_one('.CloudflareImage.header-image')
                img_link =  img_element['src']
            if course_soup.select_one('.CloudflareImage.video-thumb'):
                img_element = course_soup.select_one('.CloudflareImage.video-thumb')
                img_link =  img_element['src']

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

        print(f"Courses from edX : {len(courses)}")
        return courses

    except Exception as e:
        print(f"Error scraping course link '{course_link}' :")
        print(e)
        print(f"Courses from edX : {len(courses)}")
        return courses

    finally:
        driver.quit()