[![Build Status](https://travis-ci.org/Arthur236/shopping-list-api.svg?branch=master)](https://travis-ci.org/Arthur236/shopping-list-api)   [![Coverage Status](https://coveralls.io/repos/github/Arthur236/shopping-list-api/badge.svg?branch=master)](https://coveralls.io/github/Arthur236/shopping-list-api?branch=master)   [![Code Health](https://landscape.io/github/Arthur236/shopping-list-api/master/landscape.svg?style=flat)](https://landscape.io/github/Arthur236/shopping-list-api/master)   [![Codacy Badge](https://api.codacy.com/project/badge/Grade/78995aa52f52492187af656f7c2cc06f)](https://www.codacy.com/app/Arthur236/shopping-list-api?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Arthur236/shopping-list-api&amp;utm_campaign=Badge_Grade)

# Shopping List API

A simple api to a shopping list application

## Features

* Creation of users
* Creation of shopping lists
* Addition of items to a shopping list

## Getting Started

### Installation and setup
Clone this repository
&gt;https://github.com/Arthur236/shopping-list-api

### Navigate to the project directory

&gt;cd _path to project directory_

### Install Python

&gt;https://www.python.org/downloads/release/python-362/

### Install virtualenv

&gt;pip install virtualenv

### Install virtualenvwrapper-win

&gt;pip install virtualenvwrapper-win

### Make a virtual environment

&gt;mkvirtualenv _project-name_

### Connect your project to the virtual environment

&gt;setprojectdir .

This will ensure the next time you activate your environment, you will be automatically moved to the directory

### Activate your environment

&gt;workon _project-name_

### Requirements

All the requirements for the project are located in the requirements.txt file in the project root.  
You can automatically install all of them by typing:  

&gt;pip install -r requirements.txt

### Initialize, migrate and update the database:
&gt;python manage.py db init  
 python manage.py db migrate  
 python manage.py db upgrade
 
 ### Testing the application
 &gt;python manage.py test
 
 ### Running the application
 First you must export or set the environment variables like so:
 &gt;set FLASK_APP=run.py  
set SECRET=some_random_long_text  
set APP_SETTINGS=development  
set DATABASE_URL=postgresql://_postgres-user_:_password_@localhost/_db-name_

Then run the application using:
&gt;flask run

### Application end points
Access the endpoints using your preferred client e.g. Postman

| Resource URL                                                   | Method  | Description              | Requires Token |
|----------------------------------------------------------------|---------|--------------------------|----------------|
| /auth/register                                                 | POST    | User registration        | FALSE          |
| /auth/login                                                    | POST    | User login               | FALSE          |
| /shopping_lists                                                | POST    | Create shopping list     | TRUE           |
| /shopping_lists                                                | GET     | Get shopping lists       | TRUE           |
| /shopping_list/&lt;int:list_id&gt;                             | GET     | Get a shopping list      | TRUE           |
| /shopping_list/&lt;int:list_id&gt;                             | PUT     | Edit a shopping list     | TRUE           |
| /shopping_list/&lt;int:list_id&gt;                             | DELETE  | Delete a shopping list   | TRUE           |
| /shopping_list/&lt;int:list_id&gt;/items                       | POST    | Create a list item       | TRUE           |
| /shopping_list/&lt;int:list_id&gt;/items                       | GET     | Get list items           | TRUE           |
| /shopping_list/&lt;int:list_id&gt;/items/&lt;int:item_id&gt;   | GET     | Get a list item          | TRUE           |
| /shopping_list/&lt;int:list_id&gt;/items/&lt;int:item_id&gt;   | PUT     | Edit a list item         | TRUE           |
| /shopping_list/&lt;int:list_id&gt;/items/&lt;int:item_id&gt;   | DELETE  | Delete a list item       | TRUE           |
