from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from langdetect import detect, LangDetectException
import langcodes

# This function will allow us to navigate through all the pages and get all the courses's links
def get_links(driver, base_url):
    course_links = []
    driver.get(base_url)
    time.sleep(3)

    while True:
        # If there are no results for the search made, we break from the loop
        if driver.find_elements(By.CSS_SELECTOR, 'span[data-testid="no-results-message"]'):
            break
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.gamut-163x3fc-TabPanels.ebokd7t0')))
        soup = BeautifulSoup(driver.page_source, 'lxml')
        course_elements = soup.select('a.gamut-1p88oxo-AnchorBase.e14vpv2g0')

        for course_element in course_elements:
            link = course_element.get('href')
            if link:
                course_links.append(f"https://www.codecademy.com{link}")

        # Check for the next page link
        next_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Navigate forward to page')]")
        if next_button.is_enabled():
            next_button.click()
            time.sleep(3)
        else:
            break
    return course_links

def scrape_codecademy_courses(query):
    driver = webdriver.Chrome()
    base_url = f"https://www.codecademy.com/search?query={query}"
    courses = []
    # Unfortunately this site doesn't have an image for each course, so we give them the same image of the logo of Codecademy
    img_link = "https://sm.pcmag.com/pcmag_uk/review/c/codecademy/codecademy_rps1.png"
    course_links = get_links(driver, base_url)
    if len(course_links) == 0:
        print('No courses found in Codecademy')
        return courses

    try:
        # After we get all the links we navigate to them one by one and extract the data needed
        for course_link in course_links:
            driver.get(course_link)
            time.sleep(3)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.gamut-o2lsrx-StyledText.e8i0p5k0')))
            except:
                print(f"Error loading course link: '{course_link}'")
                continue

            course_soup = BeautifulSoup(driver.page_source, 'lxml')
            title = course_soup.select_one('h1.gamut-o2lsrx-StyledText.e8i0p5k0').get_text(strip=True).replace('Front End', 'Front-End').strip().replace('Back End', 'Back-End').strip() if course_soup.select_one('h1.gamut-o2lsrx-StyledText.e8i0p5k0') else 'Title not found'
            # There are 2 elements that they may contain the description so we check them both
            description = 'Description not found'
            if course_soup.select('p.styles_p__TNq46.e15s334q0.gamut-1g2s055-StyledText.e8i0p5k0'):
                paragraphs = course_soup.select('p.styles_p__TNq46.e15s334q0.gamut-1g2s055-StyledText.e8i0p5k0')
                description = '\n'.join([paragraph.get_text(strip=True) for paragraph in paragraphs])
            if description == 'Description not found'and course_soup.select('p.gamut-1e8q07v-StyledText.e8i0p5k0'):
                paragraphs = course_soup.select('p.gamut-1e8q07v-StyledText.e8i0p5k0')
                description = '\n'.join([paragraph.get_text(strip=True) for paragraph in paragraphs])
            # Some courses don't mention the instructor so we initiate it as 'Codecademy Staff' then look if the instructor is actually mentioned or not
            instructor = 'Codecademy Staff'
            if course_soup.select('div.gamut-1ur6bbb-StyledText.e8i0p5k0'):
                instructor = course_soup.select_one('div.gamut-1ur6bbb-StyledText.e8i0p5k0').get_text(strip=True)
            # The duration and level are both stored in the same element, so we look for them using the name of each piece of information given
            duration = 'Duration not found'
            level = 'Level not found'
            information_elements = course_soup.select('li.gamut-1o4sy9-FlexBox.e1tc6bzh0')
            if information_elements:
                for information_element in information_elements:
                    information = information_element.select_one('div.gamut-1a3zqkd-Box.e6euxnl0')
                    information_name = information.select_one('p.gamut-1u67vsd-StyledText.e8i0p5k0')
                    if information_name.get_text(strip=True) == 'Skill level':
                        level = information.select_one('span.gamut-ru06wy-StyledText.e8i0p5k0').get_text(strip=True)
                    elif information_name.get_text(strip=True) == 'Time to complete':
                        duration = information.select_one('span.gamut-ru06wy-StyledText.e8i0p5k0').get_text(strip=True)
            # We locate the elements containing the skills then join them together
            skills_list = course_soup.select('li.styles_li__mfNCB.gamut-8b8ret.es7j2620')
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
            # For the price, we try to locate the element that is only present if the course is free
            if course_soup.select('div.gamut-atx9ur-BadgeBase.emeh29k0'):
                price = 'Free'
            else:
                price = 'Paid'

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

        print(f"Courses from Codecademy: {len(courses)}")
        return courses

    except Exception as e:
        print(f"Error scraping course link '{course_link}' :")
        print(e)
        print(f"Courses from Codecademy: {len(courses)}")
        return courses

    finally:
        driver.quit()