import sqlite3
from werkzeug.security import generate_password_hash
import os

DB_URL = os.environ.get("DB_URL")


class CreateDB:
    def __init__(self):
        # CREATE DB
        self.db = sqlite3.connect(rf"{DB_URL}", check_same_thread=False, timeout=30)
        self.cursor = self.db.cursor()
        self.create_blog_post_table()
        self.create_comment_table()
        self.create_token_table()
        self.create_user_table()
        self.create_project_table()

    # ############# CREATE COMMENT TABLE IN DB #############################
    def create_comment_table(self):
        check_comment_tlb = \
            self.db.execute(
                "SELECT count(*) FROM sqlite_master where tbl_name = 'comment' and type = 'table'; ").fetchone()[0]
        # print(f"Check Comment Post table: {check_comment_tlb}")

        if check_comment_tlb == 0:
            self.cursor.execute(
                "CREATE TABLE comment (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, "
                "user_name VARCHAR(250) NOT NULL, text TEXT NOT NULL, date DATE NOT NULL, post_id INTEGER, "
                "CONSTRAINT fk_comment_comment_id FOREIGN KEY (user_id) REFERENCES user(id), "
                "CONSTRAINT fk_comment_post_id FOREIGN KEY (post_id) REFERENCES blog_post(id));")
        else:
            print('User table exists!')

    # ############# CREATE BLOG_POST TABLE IN DB #############################
    def create_blog_post_table(self):
        # CREATE TABLE
        # Check if movies table exists in the database:
        check_blog_post_tlb = self.db.execute(
            "SELECT count(*) FROM sqlite_master where tbl_name = 'blog_post' and type = 'table'; ").fetchone()[0]
        # print(f"Check Blog Post table: {check_blog_post_tlb}")
        if check_blog_post_tlb == 0:
            self.cursor.execute(
                "CREATE TABLE blog_post (id INTEGER PRIMARY KEY, author VARCHAR(250) NOT NULL, "
                "author_id integer NOT NULL, title VARCHAR(250) NOT NULL UNIQUE, "
                "subtitle VARCHAR(250) NOT NULL, date DATE NOT NULL, body TEXT NOT NULL, "
                "img_url VARCHAR(250), CONSTRAINT fk_post_user_id FOREIGN KEY (author_id) REFERENCES user(id)); ")
        else:
            print('Table found!')

    # ############# CREATE token TABLE IN DB #############################

    def create_token_table(self):
        check_token_tlb = \
            self.db.execute(
                "SELECT count(*) FROM sqlite_master where tbl_name = 'token' and type = 'table'; ").fetchone()[0]
        # print(f"Check User table: {check_token_tlb}")

        if check_token_tlb == 0:
            self.cursor.execute("CREATE TABLE token (token_id INTEGER PRIMARY KEY, user_id INTEGER, token VARCHAR(100) "
                                "NOT NULL, expiration_datetime DATETIME NOT NULL, token_used BOOL DEFAULT 0,"
                                "CONSTRAINT fk_token_user_id FOREIGN KEY (user_id) REFERENCES token(id));")
        else:
            print('User table exists!')

    # ############# CREATE USER TABLE IN DB #############################
    def create_user_table(self):
        check_user_tlb = \
            self.db.execute(
                "SELECT count(*) FROM sqlite_master where tbl_name = 'user' and type = 'table'; ").fetchone()[0]
        # print(f"Check User table: {check_user_tlb}")

        if check_user_tlb == 0:
            self.cursor.execute(
                "CREATE TABLE user (id INTEGER PRIMARY KEY, email VARCHAR(100) NOT NULL UNIQUE, "
                "password VARCHAR(100) NOT NULL, name VARCHAR(250) NOT NULL, admin_role BIT(1) DEFAULT 0, "
                "verification_code INTEGER DEFAULT 0);")

            hash_and_salted_password = generate_password_hash(password='admin123$$',
                                                              method='pbkdf2:sha256', salt_length=8)

            sql_user_insert = "INSERT INTO user (email, password, name, admin_role) VALUES (?, ?, ?, ?)"
            user_insert_param = ('appstechemail@gmail.com', hash_and_salted_password, 'Admin-User', 1)
            self.cursor.execute(sql_user_insert, user_insert_param)
            self.db.commit()
        else:
            print('User table exists!')

    # ############# CREATE Project TABLE IN DB #############################
    def create_project_table(self):
        check_project_tlb = \
            self.db.execute(
                "SELECT count(*) FROM sqlite_master where tbl_name = 'project' and type = 'table'; ").fetchone()[0]
        # print(f"Check Project table: {check_project_tlb}")

        if check_project_tlb == 0:
            self.cursor.execute(
                "CREATE TABLE project (id INTEGER PRIMARY KEY, project_id VARCHAR(20) NOT NULL, "
                "project_name VARCHAR(100) NOT NULL, about TEXT NOT NULL, "
                "last_updated_on DATE NOT NULL DEFAULT CURRENT_TIMESTAMP);")

            sql_user_insert = "INSERT INTO project (project_id, project_name, about) VALUES (?, ?, ?)"
            user_insert_param = ('PMHUT001', 'PMHut Project', 'XYZ')
            self.cursor.execute(sql_user_insert, user_insert_param)
            self.db.commit()
        else:
            print('Project table exists!')

    # ############# CREATE Project TABLE IN DB #############################
