from sites_scrapers.edX_scraper import scrape_edx_courses
from sites_scrapers.coursera_scraper import scrape_coursera_courses
from sites_scrapers.pluralsight_scraper import scrape_pluralsight_courses
from sites_scrapers.udacity_scraper import scrape_udacity_courses
from sites_scrapers.codecademy_scraper import scrape_codecademy_courses
from sites_scrapers.alison_scraper import scrape_alison_courses
from sites_scrapers.cbtnuggets_scraper import scrape_cbtnuggets_courses

# This function will combine all the results obtained from different sites
def combine_courses(query):
    edx_courses = scrape_edx_courses(query)
    coursera_courses = scrape_coursera_courses(query)
    pluralsight_courses = scrape_pluralsight_courses(query)
    udacity_courses = scrape_udacity_courses(query)
    codecademy_courses = scrape_codecademy_courses(query)
    alison_courses = scrape_alison_courses(query)
    cbtnuggets_courses = scrape_cbtnuggets_courses(query)

    all_courses = (
        edx_courses +
        coursera_courses +
        pluralsight_courses +
        udacity_courses +
        codecademy_courses +
        alison_courses +
        cbtnuggets_courses
            )
    print("Total courses found:", len(all_courses))

    return all_courses