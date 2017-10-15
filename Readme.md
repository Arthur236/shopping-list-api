[![Build Status](https://travis-ci.org/Arthur236/shopping-list-api.svg?branch=master)](https://travis-ci.org/Arthur236/shopping-list-api)   [![Code Health](https://landscape.io/github/Arthur236/shopping-list-api/master/landscape.svg?style=flat)](https://landscape.io/github/Arthur236/shopping-list-api/master)   [![Coverage Status](https://coveralls.io/repos/github/Arthur236/shopping-list-api/badge.svg?branch=master)](https://coveralls.io/github/Arthur236/shopping-list-api?branch=master)   [![Codacy Badge](https://api.codacy.com/project/badge/Grade/78995aa52f52492187af656f7c2cc06f)](https://www.codacy.com/app/Arthur236/shopping-list-api?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Arthur236/shopping-list-api&amp;utm_campaign=Badge_Grade)

# Shopping List API

A simple api to a shopping list application

## Features

* Creation of users
* Creation of shopping lists
* Addition of items to a shopping list
* Ability to share lists with friends

## Documentation

The documentation for this API can be found at: 
>https://awesome-shopping-list-api.herokuapp.com/v1

## Getting Started

### Installation and setup
Clone this repository
>https://github.com/Arthur236/shopping-list-api

### Navigate to the project directory

>cd _path to project directory_

### Install Python

>https://www.python.org/downloads/release/python-362/

### Install virtualenv

>pip install virtualenv

### Install virtualenvwrapper-win

>pip install virtualenvwrapper-win

### Make a virtual environment

>mkvirtualenv _project-name_

### Connect your project to the virtual environment

>setprojectdir .

This will ensure the next time you activate your environment, you will be automatically moved to the directory

### Activate your environment

>workon _project-name_

### Requirements

All the requirements for the project are located in the requirements.txt file in the project root.  
You can automatically install all of them by typing:  

>pip install -r requirements.txt

### Initialize, migrate and update the database:
>python manage.py db init  
 python manage.py db migrate  
 python manage.py db upgrade
 
 ### Testing the application
 >python manage.py test
 
 ### Running the application
 First you must export or set the environment variables like so:
 >set FLASK_APP=run.py  
set SECRET=some_random_long_text  
set APP_SETTINGS=development  
set DATABASE_URL=postgresql://_postgres-user_:_password_@localhost/_db-name_

Then run the application using:
>flask run

### Application end points
Access the endpoints using your preferred client e.g. Postman

| Resource URL                                               | Method  | Description              | Requires Token |
|------------------------------------------------------------|---------|--------------------------|----------------|
| /v1/auth/register                                          | POST    | User registration        | FALSE          |
| /v1/auth/login                                             | POST    | User login               | FALSE          |
| /v1/auth/reset                                             | POST    | Generate reset token     | FALSE          |
| /v1/auth/password/&lt;token&gt;                            | PUT     | Reset password           | TRUE           |
| /v1/users                                                  | GET     | Search users             | TRUE           |
| /v1/users/&lt;user_id&gt;                                  | GET     | Get user profile         | TRUE           |
| /v1/users/&lt;user_id&gt;                                  | PUT     | Update user profile      | TRUE           |
| /v1/users/&lt;user_id&gt;                                  | DELETE  | Deactivate account       | TRUE           |
| /v1/admin/users                                            | GET     | Get all users            | TRUE           |
| /v1/admin/users/&lt;user_id&gt;                            | GET     | Get a specific user      | TRUE           |
| /v1/admin/users/&lt;user_id&gt;                            | DELETE  | Delete a specific user   | TRUE           |
| /v1/shopping_lists                                         | POST    | Create shopping list     | TRUE           |
| /v1/shopping_lists                                         | GET     | Get shopping lists       | TRUE           |
| /v1/shopping_lists/&lt;list_id&gt;                         | GET     | Get a shopping list      | TRUE           |
| /v1/shopping_lists/&lt;list_id&gt;                         | PUT     | Edit a shopping list     | TRUE           |
| /v1/shopping_lists/&lt;list_id&gt;                         | DELETE  | Delete a shopping list   | TRUE           |
| /v1/shopping_lists/&lt;list_id&gt;/items                   | POST    | Create a list item       | TRUE           |
| /v1/shopping_lists/&lt;list_id&gt;/items                   | GET     | Get list items           | TRUE           |
| /v1/shopping_lists/&lt;list_id&gt;/items/&lt;item_id&gt;   | GET     | Get a list item          | TRUE           |
| /v1/shopping_lists/&lt;list_id&gt;/items/&lt;item_id&gt;   | PUT     | Edit a list item         | TRUE           |
| /v1/shopping_lists/&lt;list_id&gt;/items/&lt;item_id&gt;   | DELETE  | Delete a list item       | TRUE           |
| /v1/friends                                                | GET     | Get all friends          | TRUE           |
| /v1/friends                                                | POST    | Send friend request      | TRUE           |
| /v1/friends/&lt;friend_id&gt;                              | PUT     | Accept friend request    | TRUE           |
| /v1/friends/&lt;friend_id&gt;                              | DELETE  | Delete a list item       | TRUE           |
| /v1/friends/requests                                       | GET     | Get friend requests      | TRUE           |
| /v1/shopping_lists/share                                   | GET     | Get shared lists         | TRUE           |
| /v1/shopping_lists/share                                   | POST    | Share a list             | TRUE           |
| /v1/shopping_lists/share/&lt;list_id&gt;                   | DELETE  | Stop sharing a list      | TRUE           |
| /v1/shopping_lists/share/&lt;list_id&gt;/items             | GET     | Get shared list items    | TRUE           |
