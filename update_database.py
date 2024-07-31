from mysql.connector import Error
from data_collector import combine_courses
from remove_redundancy import filter_unique_courses
from insert_courses_to_database import insert_course, create_connection

# This function will help us to get all the skills stored in the database and make them into a string separated by ','
def get_skills(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT skills FROM course")
        skills_rows = cursor.fetchall()
        skills = ','.join(row[0] for row in skills_rows)
        return skills
    except Error as e:
        print(f"Error retrieving skills: {e}")
        return []

# This function will help search for these skills and insert every course related to them into the database
def insert_skill(connection):
    skills = get_skills(connection)
    if not skills:
        print("No skills found in the database.")
        return

    # We split the String into a set of distinct skills
    skills_list = set(skills.split(','))

    # We will then add every course related to the skills into the database
    for skill in skills_list:
        print(f"For '{skill}' :")
        all_courses = combine_courses(skill)
        unique_courses = filter_unique_courses(all_courses)
        for course in unique_courses:
            insert_course(connection, course)

# Now we create the function main that will execute all the above
def main():
    try:
        connection = create_connection("localhost", "root", "", "plateforme_tutoriels")
        if connection:
            insert_skill(connection)
        else:
            print("Failed to connect to database.")
    finally:
        if connection:
            connection.close()
            print("MySQL connection closed")

if __name__ == "__main__":
    main()

# To make this script update the database automatically every month we should do the next steps :

# If windows :
#   Press 'Win + R' then type 'taskschd.msc'
#   Click 'Create Basic Task' and write the name and description of the task
#   Choose "Monthly", select all the months and select the 1 day then for the time choose 00:00:00
#   Choose "Start a program" and browse to the path of 'python.exe' then in the "Add arguments" field, enter the path of this script

# If Linux:
#   Open a terminal and type 'crontab -e'
#   Add this line : "0 0 1 * * path_to_python path_to_script" then save the file