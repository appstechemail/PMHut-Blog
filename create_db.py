import sqlite3
from werkzeug.security import generate_password_hash
import os
import psycopg2

DB_HOSTNAME = os.environ.get("DB_HOSTNAME")
DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_URL = os.environ.get('DB_URL')
DB_DATABASE = os.environ.get('DB_DATABASE')


class CreateDB:
    def __init__(self):
        # CREATE DB
        self.db = psycopg2.connect(host=DB_HOSTNAME, database=DB_DATABASE, user=DB_USERNAME, password=DB_PASSWORD)
        self.cursor = self.db.cursor()
        self.create_project_table()
        self.create_user_table()
        self.create_token_table()
        self.create_blog_post_table()
        self.create_comment_table()

    # ############# CREATE Project TABLE IN DB #############################
    def create_project_table(self):
        # ### POSTGRESQL

        check_project_data = ("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'project' AND "
                              "table_type = 'BASE TABLE'; ")
        self.cursor.execute(check_project_data)
        check_project_tlb = self.cursor.fetchone()
        if check_project_tlb[0] == 0:
            self.cursor.execute(
                "CREATE TABLE project (id INTEGER PRIMARY KEY, project_id VARCHAR(20) NOT NULL, "
                "project_name VARCHAR(100) NOT NULL, about TEXT NOT NULL, "
                "last_updated_on DATE NOT NULL DEFAULT CURRENT_TIMESTAMP);")

            sql_user_insert = "INSERT INTO project (id, project_id, project_name, about) VALUES (%s, %s, %s, %s)"
            user_insert_param = (1, 'PMHUT001', 'PMHut Project', 'XYZ')
            self.cursor.execute(sql_user_insert, user_insert_param)
            self.db.commit()
        else:
            print('Project table exists!')

    # ############# CREATE USER TABLE IN DB #############################
    def create_user_table(self):
        #  POSTGRESQL

        check_user_data = ("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'user' AND "
                           "table_type = 'BASE TABLE'; ")
        self.cursor.execute(check_user_data)
        check_user_tlb = self.cursor.fetchone()
        if check_user_tlb[0] == 0:
            self.cursor.execute(
                "CREATE TABLE 'user' (id INTEGER PRIMARY KEY, email VARCHAR(100) NOT NULL UNIQUE, "
                "password VARCHAR(100) NOT NULL, name VARCHAR(250) NOT NULL, admin_role BIT(1) DEFAULT 0, "
                "verification_code INTEGER DEFAULT 0);")

            hash_and_salted_password = generate_password_hash(password='admin123$$',
                                                              method='pbkdf2:sha256', salt_length=8)

            sql_user_insert = "INSERT INTO user (id, email, password, name, admin_role) VALUES (%s, %s, %s, %s, %s)"
            user_insert_param = (1, 'appstechemail@gmail.com', hash_and_salted_password, 'Admin-User', 1)
            self.cursor.execute(sql_user_insert, user_insert_param)
            self.db.commit()
        else:
            print('User table exists!')

    # ############# CREATE token TABLE IN DB #############################
    def create_token_table(self):
        # POSTGRESQL
        check_token_data = ("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'token' AND "
                            "table_type = 'BASE TABLE'; ")
        self.cursor.execute(check_token_data)
        check_token_tlb = self.cursor.fetchone()
        if check_token_tlb[0] == 0:
            self.cursor.execute("CREATE TABLE token (token_id INTEGER PRIMARY KEY, user_id INTEGER, token VARCHAR(100) "
                                "NOT NULL, expiration_datetime DATETIME NOT NULL, token_used BOOL DEFAULT 0,"
                                "CONSTRAINT fk_token_user_id FOREIGN KEY (user_id) REFERENCES token(id));")
        else:
            print('User table exists!')

    # ############# CREATE BLOG_POST TABLE IN DB #############################

    def create_blog_post_table(self):
        # POSTGRESQL
        # print(f"Check Blog Post table: {check_blog_post_tlb}")
        check_blog_post_data = ("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'blog_post' AND "
                                "table_type = 'BASE TABLE'; ")
        self.cursor.execute(check_blog_post_data)
        check_blog_post_tlb = self.cursor.fetchone()
        if check_blog_post_tlb[0] == 0:
            self.cursor.execute(
                "CREATE TABLE blog_post (id INTEGER PRIMARY KEY, author VARCHAR(250) NOT NULL, "
                "author_id integer NOT NULL, title VARCHAR(250) NOT NULL UNIQUE, "
                "subtitle VARCHAR(250) NOT NULL, date DATE NOT NULL, body TEXT NOT NULL, "
                "img_url VARCHAR(250), CONSTRAINT fk_post_user_id FOREIGN KEY (author_id) REFERENCES user(id)); ")
        else:
            print('Table found!')

    # ############# CREATE COMMENT TABLE IN DB #############################
    def create_comment_table(self):
        # POSTGRESQL
        check_comment_data = ("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'comment' AND "
                              "table_type = 'BASE TABLE'; ")
        self.cursor.execute(check_comment_data)
        check_comment_tlb = self.cursor.fetchone()
        if check_comment_tlb[0] == 0:
            self.cursor.execute(
                "CREATE TABLE comment (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, "
                "user_name VARCHAR(250) NOT NULL, text TEXT NOT NULL, date DATE NOT NULL, post_id INTEGER, "
                "CONSTRAINT fk_comment_comment_id FOREIGN KEY (user_id) REFERENCES user(id), "
                "CONSTRAINT fk_comment_post_id FOREIGN KEY (post_id) REFERENCES blog_post(id));")
        else:
            print('User table exists!')
