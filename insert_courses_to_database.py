import mysql.connector
from mysql.connector import Error

# We need first to be connected with our database
def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            password=user_password,
            database=db_name
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection

# This function will make sure that the course that's going be added doesn't exist in the database
def course_exists(connection, title, instructor, language):
    cursor = connection.cursor()
    # We count the number of courses that have the same name, instructor and language of the course that's going be added
    query = "SELECT COUNT(*) FROM course WHERE title = %s AND instructor LIKE %s AND language = %s"
    cursor.execute(query, (title, f"%{instructor}%",language))
    result = cursor.fetchone()
    return result[0] > 0

# This is the function that's going to add the new courses to the database
def insert_course(connection, course):
    if course_exists(connection, course['title'], course['instructor'],course['language']):
        print(f"Course '{course['title']}' by '{course['instructor']}' in {course['language']} already exists in the database : {course['course_link']}")
        return

    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO course (title, description, instructor, duration, skills, level, language, price, img_link, course_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                course['title'],
                course['description'],
                course['instructor'],
                course['duration'],
                course['skills'],
                course['level'],
                course['language'],
                course['price'],
                course['img_link'],
                course['course_link']
            )
        )
        connection.commit()
    except Error as e:
        print(f"The error '{e}' occurred while inserting course: {course['title']} '{course['course_link']}'")