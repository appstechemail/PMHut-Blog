import sqlite3
from create_db import CreateDB


class BlogList:
    def __init__(self):
        self.all_blog_posts = []
        self.api_key = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
        self.db = None
        self.cursor = None

    def get_db(self):
        if not self.db:
            self.db = CreateDB().db
        return self.db

    def get_cursor(self):
        if not self.cursor:
            self.cursor = self.get_db().cursor()
        return self.cursor

    def execute_query(self, sql, operation_type='query', values=None):
        try:
            cursor = self.get_cursor()
            if values:
                cursor.execute(sql, values)
            else:
                cursor.execute(sql)
            if operation_type == 'query':
                rows = cursor.fetchall()
                return rows
            elif operation_type == 'insert':
                self.get_db().commit()
                print("Record inserted successfully.")
            elif operation_type == 'update':
                self.get_db().commit()
                print("Record updated successfully.")
            elif operation_type == 'delete':
                self.get_db().commit()
                print("Record deleted successfully.")
        except sqlite3.Error as e:
            print("SQLite error:", e.args[0])  # Print the error message
            # Log the error
            # Rollback transaction if needed
        finally:
            pass

    def close_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()

    def blog_posts(self):
        self.get_cursor().row_factory = sqlite3.Row
        sql_post_query = 'SELECT * from blog_post;'
        blog_posts_data = self.execute_query(sql_post_query)
        # print(f"Blog Post Data: {blog_posts_data}")
        if blog_posts_data:
            # print(f"Blog Post Data: {blog_posts_data}")
            self.all_blog_posts = [dict(post) for post in blog_posts_data]
            # print(f"Self Post Data: {self.all_blog_posts}")
        else:
            self.all_blog_posts = []

        return self.all_blog_posts

    def show_blog_post(self, post_id):
        self.get_cursor().row_factory = sqlite3.Row
        sql_post_query = 'SELECT * from blog_post where id = ?;'
        blog_post_rec = self.execute_query(sql_post_query, values=post_id)
        # print(f"Blog Post Rec {blog_post_rec}")
        if blog_post_rec:
            blog_post = [dict(rec) for rec in blog_post_rec]
            # print(f"Blog Post: {blog_post}")
            return blog_post

    def new_blog_post(self, param):
        sql_insert = ("INSERT INTO blog_post(author_id, title, subtitle, date, body,  author, img_url) "
                      "values(?, ?, ?, ?, ?, ?, ?);")
        self.execute_query(sql_insert, operation_type='insert', values=param)

    def update_blog_post(self, param):
        sql_update = "UPDATE blog_post SET title=?, subtitle=?, body=?, author=?, img_url=? WHERE id = ?;"
        self.execute_query(sql_update, operation_type='update', values=param)

    def delete_blog_post(self, del_post_id):
        # if api_key == self.api_key:
        sql_delete_post = "DELETE FROM blog_post WHERE id = ?;"
        self.execute_query(sql_delete_post, operation_type='delete', values=del_post_id)
        sql_delete_comment = "DELETE FROM comment WHERE post_id = ?;"
        self.execute_query(sql_delete_comment, operation_type='delete', values=del_post_id)

    def delete_comment(self, del_comment_id, post_id):
        # if api_key == self.api_key:
        sql_delete_comment = "DELETE FROM comment WHERE id = ? and post_id = ?;"
        param = (del_comment_id, post_id)
        self.execute_query(sql_delete_comment, operation_type='delete', values=param)