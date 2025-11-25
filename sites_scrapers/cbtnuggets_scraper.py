from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from langdetect import detect, LangDetectException
import langcodes

# This function will allow us to navigate through all the pages and get all the courses's links, levels and skills
def get_course_informations(driver, query):
    base_url = f"https://www.cbtnuggets.com/search?q={query}"
    driver.get(base_url)
    time.sleep(3)

    course_links = []
    levels = []
    skills = []
    '''
    while True:
        # Click 'Load more' button if available
        try:
            see_more_button = driver.find_element(By.CSS_SELECTOR, 'button.Standard-sc-u2gxo4-0.eeVhOG')
            driver.execute_script("arguments[0].click();", see_more_button)
            time.sleep(3)
        except:
            break
    '''
    soup = BeautifulSoup(driver.page_source, 'lxml')

    course_elements = soup.select('article.StyledResultItem-sc-5u8a6z-0')
    for course_element in course_elements:
        # We get first the course link
        link_element = course_element.select_one('a.StyledResultTitleLink-sc-5u8a6z-4')
        if link_element:
            course_links.append(f"https://www.cbtnuggets.com{link_element['href']}")

        # Levels and skills are in the same element, so we check for both of them
        level = 'Level not found'
        skills_text = f'{query}'
        informations_list = course_element.select('ul.StyledResultItemTags-sc-5u8a6z-7 li')
        if informations_list:
            # We start first with the level and we check if it's either beginner, intermediate, advanced or not precise
            level_text = informations_list[0].get_text(strip=True).lower()
            if 'beginner' in level_text:
                level = 'Beginner'
            elif 'intermediate' in level_text:
                level = 'Intermediate'
            elif 'advanced' in level_text:
                level = 'Advanced'
            levels.append(level)

            # For the skills we pick the domain that this course is part of because inside the course the list of skills is not precise
            # To do that we look first for the index of the number of videos of the course then we take the element that precedes it
            video_count = next((information for information in informations_list if 'videos' in information.get_text(strip=True).lower()), None)
            if video_count and len(informations_list) > 1:
                skills_element = informations_list[informations_list.index(video_count) - 1]
                skills_text = skills_element.get_text(strip=True)
            skills.append(skills_text)

    return course_links, levels, skills


def scrape_cbtnuggets_courses(query):
    driver = webdriver.Chrome()
    courses = []
    course_links, levels, skills = get_course_informations(driver, query)
    if len(course_links) == 0:
        print('No courses found in CBT Nuggets')
        return courses
    try:
        # After we get all the links we navigate to them one by one and extract the data needed
        for course_link, level, skill in zip(course_links, levels, skills):
            driver.get(course_link)
            time.sleep(3)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.InitialContent-sc-1yyossx-1.cXBMyU')))
            except:
                print(f"Error loading course link: '{course_link}'")
                continue

            course_soup = BeautifulSoup(driver.page_source, 'lxml')
            title = course_soup.select_one('div.InitialContent-sc-1yyossx-1.cXBMyU').get_text(strip=True).replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if course_soup.select_one('div.InitialContent-sc-1yyossx-1.cXBMyU') else 'Title not found'
            # The description is all the paragraphs that precede the tag <h2> so we locate them and join them together
            description = 'Description not found'
            description_element = course_soup.select_one('div.ExpandedContent-sc-1yyossx-2')
            if description_element:
                breaker = description_element.select_one('h2')
                paragraphs = []
                if breaker:
                    for element in description_element.find_all():
                        if element == breaker:
                            break
                        else:
                            paragraphs.append(element.get_text(strip=True))
                    description = '\n'.join(paragraphs)
            # The instructor is not always found so we initiate it as 'CBT Nuggets Staff' then look for it
            instructor = 'CBT Nuggets Staff'
            if course_soup.select('div.TrainerName-sc-12jawfc-3.bodApK'):
                instructor = course_soup.select_one('div.TrainerName-sc-12jawfc-3.bodApK').get_text(strip=True)
            # The duration is inside a big element that contains much information, so we look for it using 'HOUR/HOURS OF TRAINING'
            duration = 'Duration not found'
            information_elements = course_soup.select('div.CourseOverviewItemsItem-sc-11d3cub-3.byTQSd')
            if information_elements:
                for information_element in information_elements:
                    if 'HOURS OF TRAINING' in information_element.get_text(strip=True):
                        duration_element = information_element.select_one('span.CourseOverviewItemAmount-sc-11d3cub-4.bKvRdW')
                        if duration_element:
                            duration = f"{duration_element.get_text(strip=True)} Hours"
                    elif 'HOUR OF TRAINING' in information_element.get_text(strip=True):
                        duration_element = information_element.select_one('span.CourseOverviewItemAmount-sc-11d3cub-4.bKvRdW')
                        if duration_element:
                            duration = f"{duration_element.get_text(strip=True)} Hour"
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
            # Unfortunately this site doesn't have an image for each course, so we give them the same image of the logo of CBT Nuggets
            img_link = "https://f.hubspotusercontent30.net/hubfs/4306380/CBT%20Nuggets%20Logo%20%282%29.png"

            courses.append({
                'title': title,
                'description': description,
                'instructor': instructor,
                'duration': duration,
                'skills': skill,
                'level': level,
                'language': language,
                'price': price,
                'img_link': img_link,
                'course_link': course_link,
            })

        print(f"Courses from CBT Nuggets: {len(courses)}")
        return courses

    except Exception as e:
        print(f"Error scraping course link '{course_link}' :")
        print(e)
        print(f"Courses from CBT Nuggets: {len(courses)}")
        return courses

    finally:
        driver.quit()