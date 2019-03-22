from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import WishList, Base, Item, User

engine = create_engine('sqlite:///wishlist.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create dummy user, using Robo Barista from the Menu Application
user1 = User(name="Robo Barista", email="tinnyTim@udacity.com")

session.add(user1)
session.commit()

# Wish List for Robo
wish_list1 = WishList(user_id=1, name="Sample Wish List 1")

session.add(wish_list1)
session.commit()

#add 3 items to the wish list
item1 = Item(user_id=1, name="Sample Item 1",
                     price="$23", priority="Very High", wish_list=wish_list1)

session.add(item1)
session.commit()

item2 = Item(user_id=1, name="Sample Item 2",
                     price="$27", priority="Very High", wish_list=wish_list1)

session.add(item2)
session.commit()

item3 = Item(user_id=1, name="Sample Item 3",
                     price="$27", priority="Low", wish_list=wish_list1)

session.add(item3)
session.commit()



print ("added sample data")