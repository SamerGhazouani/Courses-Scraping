from data_collector import combine_courses
# This function is used to check if the instructors are the same cause their names are different for each site to another (for example we have 'Meta' in edX and 'Meta Stuff' in Coursera)
def is_substring(name1, name2):
    return name1.lower() in name2.lower() or name2.lower() in name1.lower()

def filter_unique_courses(courses):
    unique_courses = []
    # We verify each time if the course is unique or not by checking if the combination of its title, instructor and language already exists in the unique list or not
    for course in courses:
        duplicate = False
        course_identifier = (course['title'], course['instructor'], course['language'])

        for unique_course in unique_courses:
            unique_identifier = (unique_course['title'], unique_course['instructor'], unique_course['language'])

            if course_identifier[0].lower() == unique_identifier[0].lower() and is_substring(course_identifier[1], unique_identifier[1]) and course_identifier[2].lower() == unique_identifier[2].lower():
                duplicate = True
                print(f"These are the same course : '{course['course_link']}' and '{unique_course['course_link']}'")
                break

        if not duplicate:
            unique_courses.append(course)

    print(f"Total unique courses : {len(unique_courses)}")
    return unique_courses