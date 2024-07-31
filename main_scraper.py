from data_collector import combine_courses
from remove_redundancy import filter_unique_courses, save_to_txt
from insert_courses_to_database import insert_course, create_connection

# This will be our main file where we get all the courses, filter them then add them to the database
def main():
    query = 'react'
    all_courses = combine_courses(query)
    unique_courses = filter_unique_courses(all_courses)
    filename = "courses.txt"
    save_to_txt(unique_courses, filename)
    if len(unique_courses) != 0:
        connection = create_connection("localhost", "root", "", "plateforme_tutoriels")
        if connection:
            try:
                for course in unique_courses:
                    insert_course(connection, course)
            finally:
                connection.close()

if __name__ == "__main__":
    main()