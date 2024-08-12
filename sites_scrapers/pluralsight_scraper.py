from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
from langdetect import detect, LangDetectException
import langcodes

# This function will help us to get to the bottom of the page and click on "Show more" to load more courses till we get them all
def scroll_down(driver):
    while True:
        try:
            # We try to locate the button then we scroll
            button_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.search-results-section__load-button'))
            )
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 1800);")

            button = button_element.find_element(By.ID, 'search-results-section-load-more')
            driver.execute_script("arguments[0].click();", button)
            # We wait 10 seconds so the site can load
            time.sleep(10)
        except:
            #When the button is not found, that means we got all the courses and we exit this function
            break


def scrape_pluralsight_courses(query):
    base_url = f"https://www.pluralsight.com/search?q={query}&categories=course"
    driver = webdriver.Chrome()
    courses = []
    driver.get(base_url)
    try:
        WebDriverWait(driver, 70).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.search-result.columns')))
    # If there are no results for the search made, we return an empty list
    except TimeoutException:
        print('No courses found in Pluralsight')
        return courses
    scroll_down(driver)

    # After we load all the courses we save the links to the course and its image
    soup = BeautifulSoup(driver.page_source, 'lxml')
    course_elements = soup.select('a.cludo-result')
    course_links = [course_element['href'] for course_element in course_elements]
    image_elements = soup.select('div.search-result__icon img')
    image_links = [image_element['src'] for image_element in image_elements]

    try:
        # Now we navigate to the courses one by one and extract the data needed
        for i, course_link in enumerate(course_links):
            driver.get(course_link)
            time.sleep(6)
            # Sometimes the search results contain a link that's not valid anymore, so we need to check for that first
            if driver.find_elements(By.ID, 'content-error'):
                continue
            if driver.find_elements(By.CSS_SELECTOR, 'div.no-branding'):
                continue

            course_soup = BeautifulSoup(driver.page_source, 'lxml')
            # There are 2 elements that may contain the title so we check them both
            title = 'Title not found'
            title_element = course_soup.select_one('div#course-page-hero')
            if title_element:
                title = title_element.select_one('h1').get_text(strip=True).replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if title_element.select_one('h1') else 'Title not found'
            title_element = course_soup.select_one('div.course-info')
            if title == 'Title not found' and title_element:
                title = title_element.select_one('h1').get_text(strip=True).replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if title_element.select_one('h1') else 'Title not found'
            # We consider the part with the title "What you'll learn" as the description of the course
            description = 'Description not found'
            information_elements = course_soup.select('div.course-page-section')
            for information_element in information_elements:
                information_name = information_element.select_one('h2')
                if information_name and information_name.get_text(strip=True) == "What you'll learn":
                    # We extract all the paragraphs and take only the ones that are not empty
                    paragraphs = information_element.select('p')
                    description = '\n'.join([paragraph.get_text(strip=True) for paragraph in paragraphs if paragraph.get_text(strip=True)])
                    break
            # There is another way to look for the description
            information_element = course_soup.select_one('div.course-detail')
            if description == 'Description not found' and information_element:
                paragraphs = information_element.select('p')
                description = '\n'.join([paragraph.get_text(strip=True) for paragraph in paragraphs if paragraph.get_text(strip=True)])
            # There are 2 elements that may contain the instructor
            instructor = 'Pluralsight Staff'
            if course_soup.select_one('span.course-authors'):
                instructor_element = course_soup.select_one('span.course-authors')
                instructor = instructor_element.select_one('a').get_text(strip=True) if instructor_element.select_one('a') else 'Pluralsight Staff'
            if instructor == 'Pluralsight Staff' and course_soup.select('span.course-author > span'):
                instructor_element = course_soup.select_one('span.course-author > span')
                instructor = instructor_element.get_text(strip=True).replace('by ','').strip()
            # The duration and level are both stored in the same element
            information_rows = course_soup.select('div.course-info-rows')
            duration = 'Duration not found'
            level = 'Level not found'
            for information_row in information_rows:
                # We get first the name of the information extracted and check for both duration and level
                information = information_row.select('div.course-info-row-item')
                information_name = information[0].get_text(strip=True)

                if information_name == 'Level':
                    level = information[1].get_text(strip=True)
                elif information_name == 'Duration':
                    duration = information[1].get_text(strip=True)
            # There is another element containing the level and duration
            information_rows = course_soup.select('div.course-mini-row')
            for information_row in information_rows:
                information = information_row.select('div')
                information_name = information[0].get_text(strip=True)

                if information_name == 'Level':
                    level = information[1].contents[0].strip()
                elif information_name == 'Duration':
                    duration = information[1].contents[0].strip()
            # Unfortunately Pluralsight doesn't show the list of the skills that's gonna be learned so we consider the query searched as that skill
            skills = f'{query}'
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
            # All the courses on this site are paid
            price = 'Paid'
            img_link = image_links[i] if i < len(image_links) else 'Image not found'

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

        print(f"Courses from Pluralsight: {len(courses)}")
        return courses

    except Exception as e:
        print(f"Error scraping course link '{course_link}' :")
        print(e)
        print(f"Courses from Pluralsight: {len(courses)}")
        return courses

    finally:
        driver.quit()