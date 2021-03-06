from flask import(Flask,
                  render_template,
                  request,
                  redirect,
                  jsonify,
                  url_for,
                  flash)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, WishList, Item, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "WishList Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///wishlist.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create state token
# Store it in session for later validation
@app.route('/login')
def show_login():
    """
    method: shows the login page for the application
    arg:
        no arguments | app route '/login'
    return:
        renders template for login.html with session state
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    method: Uses google oath to create or check a session state and
    authorize access to all application features.
    arg:
        no arguments | app route '/gconnect'
    return:
        Authorizes user access, redirects to wish lists
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

        # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = get_user_id(login_session['email'])
    if not user_id:
        print("not user id")
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;' \
              'border-radius: 150px;-webkit-border-radius: 150px;' \
              '-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """
    method: revokes user authorization
    args:
        no arguments | app route '/gdisconnect'
    return:
        no return value
    """
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps
                                 ('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps
                                 ('Successfully disconnected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps
                                 ('Failed to revoke token for given user.',
                                  400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view WishList Information
@app.route('/wish_list/<int:wish_list_id>/list/JSON')
def wish_list_JSON(wish_list_id):
    """
    method: gets the JSON object representation of a wish list
    args:
        wish_list_id
        app route '/wish_list/<int:wish_list_id>/list/JSON'
    return:
        JSON representation of a wish list
    """
    wish_list = session.query(WishList).filter_by(id=wish_list_id).one()
    items = session.query(Item).filter_by(wish_list_id=wish_list_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/wish_list/<int:wish_list_id>/item/<int:item_id>/JSON')
def item_JSON(wish_list_id, item_id):
    """
      method: gets the JSON object representation of a wish list item
      args:
          wish_list_id, item_id
          app route '/wish_list/<int:wish_list_id>/item/<int:item_id>/JSON'
      return:
          JSON representation of a wish list item
      """
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


@app.route('/wish_list/JSON')
def all_wish_lists_JSON():
    """
      method: gets the JSON object representation of all wish lists
      args:
          no argument
          app route '/wish_list/JSON'
      return:
          JSON representation of all wish lists
      """
    all_wish_lists = session.query(WishList).all()
    return jsonify(all_wish_lists=[r.serialize for r in all_wish_lists])


# Show all wish_lists
@app.route('/')
@app.route('/wish_list/')
def show_all_wish_lists():
    """
      method: page that shows all wish lists. If the user is logged in, they
      may create a list
      args:
          app route '/'
          app route '/wish_list/'
      return:
          renders the publicwishlists.html or wishlists.html
      """
    all_wish_lists = session.query(WishList)\
        .order_by(asc(WishList.name))
    if 'username' not in login_session:
        return render_template('publicwishlists.html',
                               wish_lists=all_wish_lists)
    else:
        return render_template('wishlists.html',
                               wish_lists=all_wish_lists)


# Create a new wish_list
@app.route('/wish_list/new/', methods=['GET', 'POST'])
def add_wish_list():
    """
      method: page with form for adding a wish list
      args:
          app route '/wish_list/new/'
      return:
          renders the addwishlist.html or commits new wish list
          to the db
      """
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        new_wish_list = WishList(name=request.form['name'],
                                 user_id=login_session['user_id'])
        session.add(new_wish_list)
        flash('New WishList %s Successfully Created' % new_wish_list.name)
        session.commit()
        return redirect(url_for('show_all_wish_lists'))
    else:
        return render_template('addwishlist.html')


# Edit a wish_list
@app.route('/wish_list/<int:wish_list_id>/edit/', methods=['GET', 'POST'])
def edit_wish_list(wish_list_id):
    """
      method: page with form for editing a wish list
      args:
          app route '/wish_list/<int:wish_list_id>/edit/'
          wish_list_id
      return:
          renders the editwishlist.html or commits change to wish list
          to the db
      """
    if 'username' not in login_session:
        return redirect('/login')
    edited_wish_list = session.query(WishList).filter_by(id=wish_list_id).one()
    if edited_wish_list.user_id != login_session['user_id']:
        return "<script>function myFunction() " \
               "{alert('You are not authorized to edit this wish list. " \
               "Please create your own wish list in order to edit.');} " \
               "</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            edited_wish_list.name = request.form['name']
            flash('WishList Successfully Edited %s' % edited_wish_list.name)
            return redirect(url_for('show_all_wish_lists'))
    else:
        return render_template('editwishlist.html', wish_list=edited_wish_list)


# Delete a wish_list
@app.route('/wish_list/<int:wish_list_id>/delete/', methods=['GET', 'POST'])
def delete_wish_list(wish_list_id):
    """
      method: Deletes a wish list from the database
      args:
          app route '/wish_list/<int:wish_list_id>/delete/'
          wish_list_id
      return:
          redirects to the show wish lists page
      """
    if 'username' not in login_session:
        return redirect('/login')
    wish_list_to_delete = session.query(WishList)\
        .filter_by(id=wish_list_id).one()
    if wish_list_to_delete.user_id != login_session['user_id']:
        return "<script>function myFunction() " \
               "{alert('You are not authorized to delete this wish list. " \
               "Please create your own wish list in order to delete.');}" \
               "</script><body onload='myFunction()''>"

    session.delete(wish_list_to_delete)
    flash('%s Successfully Deleted' % wish_list_to_delete.name)
    session.commit()
    return redirect(url_for('show_all_wish_lists', wish_list_id=wish_list_id))


# Show a wish list
@app.route('/wish_list/<int:wish_list_id>/')
@app.route('/wish_list/<int:wish_list_id>/list/')
def show_wish_list(wish_list_id):
    """
      method: shows the contents of the wish list
      args:
          app route '/wish_list/<int:wish_list_id>/'
          app route '/wish_list/<int:wish_list_id>/list/'
          wish_list_id
      return:
          renders the wishlist.html page or publicwishlist.html page
      """
    wish_list = session.query(WishList).filter_by(id=wish_list_id).one()
    creator = get_user_info(wish_list.user_id)
    items = session.query(Item).filter_by(wish_list_id=wish_list_id).all()

    if 'username' not in login_session \
            or creator.id != login_session['user_id']:
        return render_template('publicwishlist.html', items=items,
                               wish_list=wish_list, creator=creator)
    else:
        return render_template('wishlist.html', items=items,
                               wish_list=wish_list, creator=creator)


# Create a new item
@app.route('/wish_list/<int:wish_list_id>/items/new/', methods=['GET', 'POST'])
def add_item(wish_list_id):
    """
    method: adds an item to a wish list using a form
    args:
        app route '/wish_list/<int:wish_list_id>/items/new/'
        wish_list_id
    return:
        renders the additem.html page or commits the new item to the db
    """
    if 'username' not in login_session:
        return redirect('/login')
    wish_list = session.query(WishList).filter_by(id=wish_list_id).one()
    if request.method == 'POST':
        new_item = Item(name=request.form['name'],
                        price=request.form['price'],
                        priority=request.form['priority'],
                        wish_list_id=wish_list_id,
                        user_id=wish_list.user_id)
        session.add(new_item)
        session.commit()
        flash('New Wish List %s Item Successfully Created' % (new_item.name))
        return redirect(url_for('show_wish_list', wish_list_id=wish_list_id))
    else:
        return render_template('additem.html', wish_list_id=wish_list_id)


# Edit an item
@app.route('/wish_list/<int:wish_list_id>/items/<int:item_id>/edit',
           methods=['GET', 'POST'])
def edit_item(wish_list_id, item_id):
    """
    method: edits an item in a wish list using a form
    args:
        app route '/wish_list/<int:wish_list_id>/items/<int:item_id>/edit'
        wish_list_id
        item_id
    return:
        renders the edititem.html page or commits the change to item to the db
    """
    if 'username' not in login_session:
        return redirect('/login')
    edited_item = session.query(Item).filter_by(id=item_id)\
        .filter_by(wish_list_id=wish_list_id).one()
    wish_list = session.query(WishList).filter_by(id=wish_list_id).one()
    if edited_item.user_id != login_session['user_id']:
        return "<script>function myFunction() " \
               "{alert('You are not authorized to edit this item. " \
               "Please create your own wish list in order to edit.');}" \
               "</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            edited_item.name = request.form['name']
        if request.form['price']:
            edited_item.price = request.form['price']
        if request.form['priority']:
            edited_item.priority = request.form['priority']
        session.add(edited_item)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('show_wish_list', wish_list_id=wish_list_id))
    else:
        return render_template('edititem.html', wish_list_id=wish_list_id,
                               item_id=item_id, item=edited_item)


# Delete an item
@app.route('/wish_list/<int:wish_list_id>/items/<int:item_id>/delete',
           methods=['GET', 'POST'])
def delete_item(wish_list_id, item_id):
    """
    method: deletes an item in a wish list using a form
    args:
        app route '/wish_list/<int:wish_list_id>/items/<int:item_id>/delete'
        wish_list_id
        item_id
    return:
        commits the item delete to the db
    """
    if 'username' not in login_session:
        return redirect('/login')
    wish_list = session.query(WishList).filter_by(id=wish_list_id).one()
    item_to_delete = session.query(Item).filter_by(id=item_id).one()
    if item_to_delete.user_id != login_session['user_id']:
        return "<script>function myFunction() " \
               "{alert('You are not authorized to delete this item. " \
               "Please create your own wish list in order to make " \
               "changes.');}</script><body onload='myFunction()''>"
    session.delete(item_to_delete)
    session.commit()
    flash('Item Successfully Deleted')
    return redirect(url_for('show_wish_list', wish_list_id=wish_list_id))


def create_user(login_session):
    """
    method: helper method that creats a user if the session holder
    isn't in the Database
    args:
        login_session
    return:
        creates user in DB
    """
    new_user = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_info(user_id):
    """
    method: helper method that gets the user info that matches the user_id
    arg:
        user_id
    return:
        user info
    """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    """
    method: helper method that gets the user_id that matches the email address
    arg:
        email address of user
    return:
        user_id
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
