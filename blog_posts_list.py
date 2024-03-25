import sqlite3
from create_db import CreateDB
import psycopg2


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
                print("Start")
            else:
                cursor.execute(sql)
            if operation_type in ['query', 'insert', 'update', 'delete']:
                if operation_type == 'query':
                    rows = cursor.fetchall()
                    return rows
                else:
                    self.get_db().commit()
                    print(f"Record {operation_type}ed successfully.")
            else:
                print(f"Invalid operation type: {operation_type}")
        except psycopg2.Error as e:
            # print("Error in Blog_Post_list.py")
            print("PostgreSQL error:", e)
            self.get_db().rollback()
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
        # Construct the SQL query to select all columns from the blog_post table
        sql_post_query = 'SELECT * FROM blog_post;'

        # Execute the SQL query and retrieve the data
        blog_posts_data = self.execute_query(sql_post_query)
        # print(f"Blog POSTS DATA: {blog_posts_data}")

        # Initialize an empty list to store blog post dictionaries
        self.all_blog_posts = []

        # Check if there are any blog posts returned from the query
        if blog_posts_data:
            # Iterate over the rows returned by the query
            for post_data in blog_posts_data:
                # Map each column to its corresponding key in the blog post dictionary

                post_dict = {
                    'id': post_data[0],
                    'author': post_data[1],
                    'author_id': post_data[2],
                    'title': post_data[3],
                    'subtitle': post_data[4],
                    'date': post_data[5],
                    'body': post_data[6],
                    'img_url': post_data[7]
                }
                # Append the dictionary representing the blog post to the list
                self.all_blog_posts.append(post_dict)

        # Return the list of blog posts
        return self.all_blog_posts

    def show_blog_post(self, post_id):
        sql_post_query = 'SELECT * from blog_post where id = %s;'
        blog_post_rec = self.execute_query(sql_post_query, values=[post_id])
        # print(f"Blog Post Rec {blog_post_rec}")
        blog_post = []
        if blog_post_rec:
            for rec in blog_post_rec:
                post_dict = {
                    'id': rec[0],
                    'author': rec[1],
                    'author_id': rec[2],
                    'title': rec[3],
                    'subtitle': rec[4],
                    'date': rec[5],
                    'body': rec[6],
                    'img_url': rec[7]
                }
                blog_post.append(post_dict)
            # print(f"Blog Post: {blog_post}")
        return blog_post

    def new_blog_post(self, param):
        # print(f"Param: {param}")
        sql_insert = ("INSERT INTO blog_post(author_id, title, subtitle, date, body,  author, img_url) "
                      "values(%s, %s, %s, %s, %s, %s, %s);")
        # print(f"Insert: {sql_insert}")
        self.execute_query(sql_insert, operation_type='insert', values=param)

    def update_blog_post(self, param):
        sql_update = "UPDATE blog_post SET title=%s, subtitle=%s, body=%s, author=%s, img_url=%s WHERE id = %s;"
        self.execute_query(sql_update, operation_type='update', values=param)

    def delete_blog_post(self, del_post_id):
        # if api_key == self.api_key:
        sql_delete_comment = "DELETE FROM comment WHERE post_id = %s;"
        self.execute_query(sql_delete_comment, operation_type='delete', values=[del_post_id])
        sql_delete_post = "DELETE FROM blog_post WHERE id = %s;"
        self.execute_query(sql_delete_post, operation_type='delete', values=[del_post_id])

    def delete_comment(self, del_comment_id, post_id):
        # if api_key == self.api_key:
        sql_delete_comment = "DELETE FROM comment WHERE id = %s and post_id = %s;"
        param = (del_comment_id, post_id)
        self.execute_query(sql_delete_comment, operation_type='delete', values=param)
