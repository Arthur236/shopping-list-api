"""
Database models
"""
from app import db
from flask_bcrypt import Bcrypt


class User(db.Model):
    """
    This class defines the users table
    """

    __tablename__ = 'users'

    # Define the columns of the users table, starting with the primary key
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(256), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    shopping_lists = db.relationship(
        'ShoppingList', order_by='ShoppingList.id', cascade="all, delete-orphan")

    def __init__(self, username, email, password):
        """
        Initialize the user with a username and a password
        """
        self.username = username
        self.email = email
        self.password = Bcrypt().generate_password_hash(password).decode()

    def password_is_valid(self, password):
        """
        Checks the password against it's hash to validates the user's password
        """
        return Bcrypt().check_password_hash(self.password, password)

    def save(self):
        """
        Save a user to the database.
        This includes creating a new user and editing one.
        """
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """
        Deletes a user
        """
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        """
        Return a representation of a user instance
        """
        return "<User: {}>".format(self.email)


class ShoppingList(db.Model):
    """
    This class represents the shopping_list table
    """

    __tablename__ = 'shopping_lists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    name = db.Column(db.String(255))
    description = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    shopping_list_items = db.relationship(
        'ShoppingListItem', order_by='ShoppingListItem.id', cascade="all, delete-orphan")
    shared_lists = db.relationship(
        'SharedList', order_by='SharedList.id', cascade="all, delete-orphan")

    def __init__(self, user_id, name, description):
        """
        Initialize the shopping list with its creator
        """
        self.user_id = user_id
        self.name = name
        self.description = description

    def save(self):
        """
        Save a shopping list
        This applies for both creating and updating a shopping list
        """
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """
        Deletes a given shopping list
        """
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        """
        Return a representation of a shopping list instance
        """
        return "<ShoppingList: {}>".format(self.name)


class ShoppingListItem(db.Model):
    """
    This class represents the shopping_list_item table
    """

    __tablename__ = 'shopping_list_items'

    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey(ShoppingList.id))
    name = db.Column(db.String(255))
    quantity = db.Column(db.Float)
    unit_price = db.Column(db.Float)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())

    def __init__(self, list_id, name, quantity, unit_price):
        """
        Initialize the shopping list item
        """
        self.list_id = list_id
        self.name = name
        self.quantity = quantity
        self.unit_price = unit_price

    def save(self):
        """
        Save a shopping list item
        """
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """
        Deletes a given shopping list item
        """
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        """
        Return a representation of a shopping list item instance
        """
        return "<ShoppingListItem: {}>".format(self.name)


class PasswordReset(db.Model):
    """
    This class defines the password resets table
    """

    __tablename__ = 'password_resets'

    # Define the columns of the users table, starting with the primary key
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), nullable=False, unique=True)
    token = db.Column(db.String(256), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, email, token):
        """
        Initialize the table
        """
        self.email = email
        self.token = token

    def save(self):
        """
        Save password reset details
        """
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """
        Deletes a given shopping list item
        """
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        """
        Return a representation of a reset instance
        """
        return "<PasswordReset: {}>".format(self.token)


class Friend(db.Model):
    """
    This class represents the friends table
    """

    __tablename__ = 'friends'

    id = db.Column(db.Integer, primary_key=True)
    user1 = db.Column(db.Integer)
    user2 = db.Column(db.Integer)
    accepted = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())

    def __init__(self, user1, user2):
        """
        Initialize friend
        """
        self.user1 = user1
        self.user2 = user2

    def save(self):
        """
        Save a friend
        """
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """
        Deletes a friend
        """
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        """
        Return a representation of a friend instance
        """
        return "<Friend: {}>".format(self.user1)


class SharedList(db.Model):
    """
    This class represents the shared lists table
    """

    __tablename__ = 'shared_lists'

    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey(ShoppingList.id))
    user1 = db.Column(db.Integer)
    user2 = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())

    def __init__(self, list_id, user1, user2):
        """
        Initialize shared list
        """
        self.list_id = list_id
        self.user1 = user1
        self.user2 = user2

    def save(self):
        """
        Save a shared list
        """
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """
        Stop sharing list
        """
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        """
        Return a representation of a shared list instance
        """
        return "<SharedList: {}>".format(self.list_id)
