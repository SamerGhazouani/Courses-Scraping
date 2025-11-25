from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
from langdetect import detect, LangDetectException
import langcodes

def scroll_down(driver):
    # Scroll to the bottom of the page where it starts generating new courses then scroll to the end
    bottom_element = driver.find_element(By.CSS_SELECTOR, "div.css-4htby8")
    driver.execute_script("arguments[0].scrollIntoView();", bottom_element)
    time.sleep(3)

    # We will calculate the height of the page and compare it every time to check if the site loaded more courses or not
    current_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 2000);")
        time.sleep(3)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == current_height:
            break
        current_height = new_height

def scrape_coursera_courses(query):
    url = f"https://www.coursera.org/search?query={query}"
    driver = webdriver.Chrome()
    courses = []
    driver.get(url)
    time.sleep(3)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.cds-9.css-5t8l4v.cds-10')))
    # If there are no results for the search made, we return an empty list
    if driver.find_elements(By.CSS_SELECTOR, 'div.css-2q69k0'):
        print('No courses found in Coursera')
        return courses
    #scroll_down(driver)

    # Get the courses links and images from the search results
    soup = BeautifulSoup(driver.page_source, 'lxml')
    course_elements = soup.select('a.cds-119.cds-113.cds-115.cds-CommonCard-titleLink.css-si869u.cds-142')
    image_elements = soup.select('div.cds-CommonCard-previewImage img')

    course_links = ["https://www.coursera.org" + course_element['href'] for course_element in course_elements]
    image_links = [image_element['src'] for image_element in image_elements]

    try:
        # Access the link of each course and extract all the information needed
        for i, course_link in enumerate(course_links):
            driver.get(course_link)
            time.sleep(3)
            # Sometimes the search results contain a link that's not valid anymore, so we need to check for that first
            if driver.find_elements(By.CSS_SELECTOR, 'div.notfound-message'):
                continue
            elif driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="MtcUcert404"]'):
                continue
            time.sleep(3)

            course_soup = BeautifulSoup(driver.page_source, 'lxml')
            # The title can be found in 4 types of elements, so we check them all
            title = course_soup.select_one('h1.cds-119.cds-Typography-base.css-1xy8ceb.cds-121').get_text(strip=True).replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if course_soup.select('h1.cds-119.cds-Typography-base.css-1xy8ceb.cds-121') else 'Title not found'
            if title=='Title not found':
                title = course_soup.select_one('h1.css-1y0db6r').get_text(strip=True).replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if course_soup.select('h1.css-1y0db6r') else 'Title not found'
            if title=='Title not found':
                title = course_soup.select_one('h1.cds-119.css-tfce48.cds-121').get_text(strip=True).replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if course_soup.select('h1.cds-119.css-tfce48.cds-121') else 'Title not found'
            if title=='Title not found':
                title = course_soup.select_one('h1.page-title').get_text(strip=True).replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if course_soup.select('h1.page-title') else 'Title not found'
            # The content with the description of the course can have the id 'details', 'modules' or 'courses' so we try to locate all the options
            description = 'Description not found'
            if course_soup.select_one('#details .content-inner') or course_soup.select_one('#modules .content-inner') or course_soup.select_one('#courses .content-inner'):
                description_element1 = course_soup.select_one('#details .content-inner')
                description_element2 = course_soup.select_one('#modules .content-inner')
                description_element3 = course_soup.select_one('#courses .content-inner')
                if description_element1:
                    description = description_element1.get_text(strip=True)
                elif description_element2:
                    description = description_element2.get_text(strip=True)
                elif description_element3:
                    description = description_element3.get_text(strip=True)
            # There's 3 other elements that may contain the description so we check them too
            if description == 'Description not found' and course_soup.select_one('div.cds-9._t741k1.css-0'):
                description_element = course_soup.select_one('div.cds-9._t741k1.css-0')
                description = description_element.select_one('div.rc-Markdown.styled').getText(strip=True)[:description_element.select_one('div.rc-Markdown.styled').getText(strip=True).find('Watch the program trailer')].strip() if description_element.select_one('div.rc-Markdown.styled') else 'Description not found'
            if description == 'Description not found' and course_soup.select_one('div.cds-9.css-0.cds-11.cds-grid-item.cds-56.cds-80 > div > div.rc-RichText.css-8lussl'):
                description_element = course_soup.select_one('div.cds-9.css-0.cds-11.cds-grid-item.cds-56.cds-80 > div > div.rc-RichText.css-8lussl')
                if description_element:
                    paragraphs = description_element.select('p')
                    if paragraphs:
                        description = '\n'.join([p.get_text(strip=True) for p in paragraphs])
                    else:
                        description = 'Description not found'
            if description == 'Description not found' and course_soup.select_one('div.rc-Markdown.styled.programHighlights.rc-Section'):
                description_element = course_soup.select_one('div.rc-Markdown.styled.programHighlights.rc-Section')
                description = description_element.select_one('p').getText(strip=True) if description_element.select_one('div.rc-Markdown.styled.programHighlights.rc-Section') else 'Description not found'
            # If the description is not found, we consider the part "What you'll learn" as the description
            # Each paragraph of the description is located in different sections, so we locate first all the elements that contain them than get one paragraph at a time
            if description == 'Description not found':
                description_elements = course_soup.select('ul.cds-9.css-7avemv.cds-10 li div.css-88ryvb')
                description = '\n'.join([f'- {element.select_one('div.rc-CML.unified-CML').get_text(strip=True)}' for element in description_elements]) if description_elements else 'Description not found'
            # There are two ways to get the instructor name: If it's written we get that text, if it's not we get the alt from their logo
            instructor = course_soup.select_one('a.cds-119.cds-113.cds-115.css-wgmz1k.cds-142').get_text(strip=True).replace('Taught by', '').strip() if course_soup.select('a.cds-119.cds-113.cds-115.css-wgmz1k.cds-142') else 'Coursera Staff'
            if instructor == 'Coursera Staff' and course_soup.select_one('div[data-test="partnerLogoContainer"].css-r5qoby img'):
                instructor = course_soup.select_one('div[data-test="partnerLogoContainer"].css-r5qoby img').get('alt', 'Coursera Staff')
            # There's 2 other elements that may contain the instructor so we check them too
            if instructor == 'Coursera Staff' and course_soup.select_one('h2.cds-119.css-l7cpy5.cds-121'):
                instructor = course_soup.select_one('h2.cds-119.css-l7cpy5.cds-121').get_text(strip=True)
            if instructor == 'Coursera Staff' and course_soup.select_one('p.partner-name'):
                instructor = course_soup.select_one('p.partner-name').get_text(strip=True)
            # The duration and level elements have the same name so we get them both and look for the specific words 'duration' and 'level'
            # Some courses don't indicate their duration and level, so we initiate the 2 variables to be 'not found'
            duration = 'Duration not found'
            level = 'Level not found'
            if course_soup.select('div.css-fk6qfz'):
                course_details = course_soup.select('div.css-fk6qfz')
                for dtl in course_details:
                    if re.search(r'\d+', dtl.get_text(strip=True)) or any(keyword in dtl.get_text(strip=True).lower() for keyword in ['horas','hora','minutos','mese','meses','año','años','ساعة','دقيقة']):
                        if dtl.get_text(strip=True).find(' (')!=-1:
                            duration = dtl.get_text(strip=True)[:dtl.get_text(strip=True).find(' (')]
                        else :
                            duration = dtl.get_text(strip=True)
                    if 'level' in dtl.get_text(strip=True):
                        level = dtl.get_text(strip=True).replace('level', '').strip()
            # If the duration is still not found, that means it's considered as a flexible schedule and we can detect there how long will it take
            if duration == 'Duration not found' and course_soup.select_one('div.css-fk6qfz:-soup-contains("Flexible schedule")'):
                flexible_schedule = course_soup.select_one('div.css-fk6qfz:-soup-contains("Flexible schedule")')
                if flexible_schedule.find_next_sibling('div', class_='css-fw9ih3'):
                    flexible_sibling = flexible_schedule.find_next_sibling('div', class_='css-fw9ih3').get_text(strip=True)
                    if re.search(r'\d+', flexible_sibling):
                        duration = flexible_sibling.split("Learn at your own pace")[0].strip()
            # We locate each element in the list of the skills then join them together in the same string
            skills_list = course_soup.select('ul.css-yk0mzy li span')
            skills = ','.join([skill.get_text(strip=True) for skill in skills_list]) if skills_list else f'{query}'
            # There is another list that may contain the skills so we check first it's existence, then we do the same as the above
            if course_soup.select('ul[data-test="course-learn"].css-lo4pby li'):
                skills_list = course_soup.select('ul[data-test="course-learn"].css-lo4pby li')
                skills = ','.join([skill.get_text(strip=True) for skill in skills_list]) if skills_list else f'{query}'
            # Some courses don't indicate the language used so we initiate it as not found then try to locate it
            language='Language not found'
            if course_soup.select('div.css-1q4m1cr'):
                language_elements = course_soup.select('div.css-1q4m1cr')
                for language_element in language_elements:
                    if language_element.select_one('p.css-4s48ix'):
                        language = language_element.select_one('p.css-4s48ix').get_text(strip=True).replace('Taught in', '').strip() if course_soup.select('div.css-1q4m1cr') else 'Language not found'
            # There are 2 elements that may contain the language, so we check them both
            if course_soup.select('div.css-drc7pp:-soup-contains("Taught in")'):
                language = course_soup.select_one('div.css-drc7pp:-soup-contains("Taught in")').get_text(strip=True).replace('Taught in', '').strip() if course_soup.select('div.css-drc7pp:-soup-contains("Taught in")') else 'Language not found'
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
            # Some courses don't tell you the price that's why we only indicate if it's free or paid
            price = 'Price not found'
            price_element = course_soup.select_one('div.with-enroll-modal')
            if price_element:
                if not course_soup.select_one('div.css-atjosz'):
                    price = 'Free'
                else:
                    if not course_soup.select_one('div.css-atjosz').contents:
                        price = 'Free'
                    else:
                        price = 'Paid'
            # Some courses have the price and duration in the same element, so if both of these attributes are still not found we need to check that element
            # The presence of theses elements means that it's a degree so we set the price as paid
            if duration == 'Duration not found' and price == 'Price not found' and course_soup.select('div._1qn2cyy7[data-test="AtAGlanceItem"]'):
                informations = course_soup.select('div._1qn2cyy7[data-test="AtAGlanceItem"]')
                price = 'Paid'
                for information in informations:
                    if information.select_one('h2[data-test="at-a-glance-title"]'):
                        information_name = information.select_one('h2[data-test="at-a-glance-title"]')
                        if any(keyword in information_name.get_text(strip=True).lower() for keyword in ['hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months','year','years','horas','hora','minutos','mese','meses','año','años','ساعة','دقيقة']):
                            duration = information_name.get_text(strip=True)
            if duration == 'Duration not found' and price == 'Price not found' and course_soup.select('div.css-cvl6l2'):
                informations = course_soup.select('div.css-cvl6l2')
                price = 'Paid'
                for information in informations:
                    if information.select_one('h2.css-af52lp'):
                        information_name = information.select_one('h2.css-af52lp')
                        if any(keyword in information_name.get_text(strip=True).lower() for keyword in ['hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months','year','years','horas','hora','minutos','mese','meses','año','años','ساعة','دقيقة']):
                            duration = information_name.get_text(strip=True)
            if duration == 'Duration not found' and price == 'Price not found' and course_soup.select('div.cds-9.css-1iuk6ex.cds-11.cds-grid-item.cds-44'):
                informations = course_soup.select('div.cds-9.css-1iuk6ex.cds-11.cds-grid-item.cds-44')
                price = 'Paid'
                for information in informations:
                    if information.select_one('h2.cds-119.cds-Typography-base.css-h1jogs.cds-121'):
                        information_name = information.select_one('h2.cds-119.cds-Typography-base.css-h1jogs.cds-121')
                        if any(keyword in information_name.get_text(strip=True).lower() for keyword in ['hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months','year','years','horas','hora','minutos','mese','meses','año','años','ساعة','دقيقة']):
                            duration = information_name.get_text(strip=True)
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

        print(f"Courses from Coursera : {len(courses)}")
        return courses

    except Exception as e:
        print(f"Error scraping course link '{course_link}' :")
        print(e)
        print(f"Courses from Coursera : {len(courses)}")
        return courses

    finally:
        driver.quit()