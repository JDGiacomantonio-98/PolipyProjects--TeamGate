# DATABASE OBJECT CLASS SPECIFICATION MODULE : SQLAlchemy builds Object-Oriented Databases
from os import listdir
from math import floor, ceil
from random import randint, random
from datetime import datetime, timedelta
from secrets import token_hex

from flask import session, current_app, url_for, flash
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as timedTokenizer
from faker import Faker
from sqlalchemy.exc import IntegrityError, OperationalError

from app import db, login_handler

if current_app.config['ENV'] in ('development', 'testing'):
	faker = Faker(['en_US', 'en_GB', 'zh_CN', 'fr_FR', 'es_ES', 'it_IT'])

# DATABASE GLOBAL FUNCTIONS #

# commits should be done for their majour part in routes and not here given that committing here can lead also to commit
# other unwanted stuff already there in the session from previous actions.


def dummy(return_obj=True, model=None, items=1, o_mass=None, db_w_test=False, cities=None):
	from app.auth.methods import hash_psw

	if type(return_obj) != bool:
		print('ERROR : single parameter only accepts bool')
		return None
	if model is None:
		print(f'Dummy objects to create : {items}\n')
		model = str(input('Which type of object do you want to create?\n'
						  '[U]ser\n'
						  '[O]wner\n'
						  '[P]ub\n'
						  '[G]roup\n'
						  '[M]atch\n\n'
						  '[Q]uit\n'
						  'select here : ')).lower()
	if model in ('q', ''):
		print('dummy() has been quited.')
		return None
	feedbacks = not(db_w_test or return_obj)
	if feedbacks:
		print('Please wait while processing dummy units ... (this might take a while)\n')
		progress = {
			0.10: 'completed : |*.............|',
			0.20: 'completed : |***...........| (20%)',
			0.30: 'completed : |****..........| (30%)',
			0.50: 'completed : |*******.......| (50%)',
			0.60: 'completed : |********......| (60%)',
			0.75: 'completed : |*********.....| (75%)',
			0.90: 'completed : |************..| (90%)'
		}
		errors = 0
		start = datetime.now()
		print('completed : |..............|')
	i = 0
	while i < items:
		if model in ('u', 'users'):
			if not cities:
				itm = User(username=faker.user_name(),
						   email=faker.email(),
						   last_active=faker.past_date(),
						   lastName=faker.last_name().lower(),
						   age=randint(16, 90),
						   sex=faker.null_boolean(),
						   country=faker.country_code(),
						   about_me=faker.text(max_nb_chars=250).lower(),
						   city=faker.city().lower(),
						   hash=hash_psw('password')
						   )
			else:
				itm = User(username=faker.user_name(),
						   email=faker.email(),
						   last_active=faker.past_date(),
						   lastName=faker.last_name().lower(),
						   age=randint(16, 90),
						   sex=faker.null_boolean(),
						   country=faker.country_code(),
						   about_me=faker.text(max_nb_chars=250).lower(),
						   city=cities[randint(0, len(cities) - 1)],
						   hash=hash_psw('password')
						   )
			if itm.sex == 'other':
				itm.firstName = faker.first_name_male()
			elif itm.sex == 'f':
				itm.firstName = faker.first_name_female()
			else:
				itm.firstName = faker.first_name_male()
			if faker.boolean(chance_of_getting_true=35):
				itm.confirmed = True
			model = 'users'
		elif model in ('o', 'owners'):
			if not cities:
				itm = Owner(username=faker.user_name(),
							email=faker.email(),
							last_active=faker.past_date(),
							lastName=faker.last_name().lower(),
							age=randint(18, 90),
							sex=faker.null_boolean(),
							about_me=faker.text(max_nb_chars=250).lower(),
							country=faker.country_code(),
							city=faker.city().lower(),
							hash=hash_psw('password'),
							subs_type=f"{randint(0, 2):02b}",
							subsExpirationDate=faker.future_date('+90d')
							)
			else:
				itm = Owner(username=faker.user_name(),
							email=faker.email(),
							last_active=faker.past_date(),
							lastName=faker.last_name().lower(),
							age=randint(18, 90),
							sex=faker.null_boolean(),
							about_me=faker.text(max_nb_chars=250).lower(),
							country=faker.country_code(),
							city=cities[randint(0, len(cities) - 1)],
							hash=hash_psw('password'),
							subs_type=f"{randint(0, 2):02b}",
							subsExpirationDate=faker.future_date('+90d')
							)
			if itm.sex == 'other':
				itm.firstName = faker.first_name_male()
			elif itm.sex == 'f':
				itm.firstName = faker.first_name_female()
			else:
				itm.firstName = faker.first_name_male()
			if faker.boolean(chance_of_getting_true=70):
				pub = dummy(model='p', db_w_test=db_w_test)
				itm.associate_pub(pub)
				itm.confirmed = True
			model = 'owners'
		elif model in ('p', 'pubs'):
			seats_max = randint(0, 200)
			itm = Pub(name=faker.text(max_nb_chars=25),
					  address=faker.street_address().lower(),
					  bookable=faker.boolean(chance_of_getting_true=40),
					  phone_num=faker.phone_number(),
					  seats_max=seats_max,
					  rating=0,
					  description=faker.text(max_nb_chars=500).lower())
			if itm.bookable:
				itm.seats_booked = seats_max - randint(0, seats_max)
			model = 'pubs'
		elif model in ('g', 'groups'):
			itm = Group(name=faker.sentence(nb_words=8))
			model = 'groups'
		elif model == 'm' or model == 'matches':
			print('We are sorry but this function is still under development!')
			itm = Match()
			model = 'matches'
		else:
			return None
		if not return_obj:
			db.session.add(itm)
			try:
				if model == 'users': # i > 0 prevents SQLAlchemy to raise an Error due to no users to query
					u_mass = User.query.count()
					if u_mass > 1:
						for _ in range(1, randint(1, u_mass)):
							# follow some users
							u = User.query.get(randint(1, u_mass))
							if u and not itm.is_following(u):
								itm.follow(u)
					if faker.boolean(chance_of_getting_true=60):
						if o_mass > 1:
							# send reservations requests
							for _ in range(1, randint(1, 7)):
								o = Owner.query.get(randint(1, o_mass))
								if o is not None and o.pub: # check for None because it could be that the query try to get an owner id which has been deleted
									itm.send_bookingReq(pub=o.pub, guests=randint(1, 6))
									db.session.add(Review(pub_id=o.pub.id, reviewer=itm.username, rating=randint(0, 5), review=faker.text(max_nb_chars=200).lower()))
									db.session.commit()
					if faker.boolean(chance_of_getting_true=35):
						# join group
						for _ in range(1, randint(1, 3)):
							g = Group(name=faker.text(max_nb_chars=15))
							itm.join_as_admin(g)
				if db_w_test:
					db.session.commit()
					db.session.delete(itm)
				db.session.commit()
				i += 1
			except IntegrityError:
				db.session.rollback()
				if feedbacks:
					errors += 1
			except OperationalError as e:
				print('(!) INFO : Have you run upgrade() from last migration file?')
				if db_w_test:
					raise RuntimeError
				else:
					return print(e)
			if feedbacks:
				try:
					print(progress[round((i / items), 2)])
				except KeyError:
					pass
		else:
			return itm
	if feedbacks:
		print(f'Completed!\n\n{items} new dummy-{model} instances has been successfully created and add to db. ({errors} errors occurred and have been corrected)')
		print(f'Connection happened on : {current_app.config["SQLALCHEMY_DATABASE_URI"]}')
		print(f'Process duration : {datetime.now() - start}')


@login_handler.user_loader
def load_user(user_id):
	if session.get('pull_from') == 'user':
		return User.query.get(user_id)
	else:
		return Owner.query.get(user_id)


# DATABASE OBJECTS STRUCTURE #
"""

(!) NOTE: there is no need to explicitly define a __init__ method on model classes.
That’s because SQLAlchemy adds an implicit constructor to all model classes which accepts keyword arguments for all its 
columns and relationships. If you decide to override the constructor for any reason, make sure to keep accepting **kwargs 
and call the super constructor with those **kwargs to preserve this behavior
"""


class Reservation(db.Model):
	"""association table to solve users-to-pubs many-to-many relationship"""
	__tablename__ = 'reservations'

	id = db.Column(db.Integer,  # need to figure out how QR code can be stored
					 primary_key=True,
					 index=True)
	date = db.Column(db.DateTime, default=datetime.now(), index=True)  # reservation timestamp
	guests = db.Column(db.Integer)  # number of people within the reservation
	confirmed = db.Column(db.Boolean, default=False, index=True)  # pub owner confirmation of the reservation
	queued = db.Column(db.Boolean, default=False, index=True)  # true if reservation is staged waiting for pub availability
	cancelled = db.Column(db.Boolean, default=False, index=True)
	by_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True, nullable=False)  # user.id foreignKey
	at_id = db.Column(db.Integer, db.ForeignKey('pubs.id'), index=True, nullable=False)  # pub.id foreignKey


class Subscription(db.Model):
	"""association table to solve users-to-groups many-to-many relationship"""
	__tablename__ = 'groups_subs'

	id = db.Column(db.Integer,
				   primary_key=True)
	member_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True, nullable=False)  # user.id foreignKey
	group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), index=True, nullable=False)  # group.id backref
	role_id = db.Column(db.Integer, db.ForeignKey('group_roles.id'),
						nullable=False)  # user allowed actions in the group
	member_since = db.Column(db.DateTime, default=datetime.utcnow())  # subscription timestamp

	def get_member_username(self):
		return User.query.get(self.member_id).username


class Follow(db.Model):
	__tablename__ = 'follows'

	follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
	following_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
	since_when = db.Column(db.DateTime, default=datetime.utcnow())

	@staticmethod
	def get_all_followed_id(user):
		followed_ids = []
		for f in user.followed.all():
			followed_ids.append(f.following_id)
		return followed_ids

	@staticmethod
	def get_all_following_id(user):
		following_ids = []
		for f in user.followers.all():
			following_ids.append(f.follower_id)
		return following_ids


class Review(db.Model):
	__tablename__ = 'reviews'

	id = db.Column(db.Integer, primary_key=True)
	pub_id = db.Column(db.Integer, db.ForeignKey('pubs.id'))
	reviewer = db.Column(db.String, nullable=False)
	rating = db.Column(db.Integer, nullable=False)
	review = db.Column(db.String(255), nullable=False)

	def get_reviewer_img(self):
		from app.main.methods import find_user

		u = find_user(self.reviewer)
		if u[0] is not None:
			if session['pull_from'] != u[1]:
				return u[0].get_imgFile(foreign_session=True)
			return u[0].get_imgFile()
		return url_for('static', filename='avatar/favicon.png')


class USER:
	id = db.Column(db.Integer,
				   primary_key=True)
	username = db.Column(db.String(10),
						 unique=True,
						 nullable=False,
						 index=True)
	email = db.Column(db.String,
					  unique=True,
					  nullable=False,
					  index=True)
	confirmed = db.Column(db.Boolean,
						  nullable=False,
						  default=False)
	last_active = db.Column(db.DateTime,
							nullable=False,
							default=datetime.utcnow())
	member_since = db.Column(db.DateTime,
							 nullable=False,
							 default=datetime.utcnow())
	acc_locked = db.Column(db.Boolean, default=False)
	file_address = db.Column(db.String(20),
							 unique=True)
	firstName = db.Column(db.String(60),
						  nullable=False)
	lastName = db.Column(db.String(60),
						 nullable=False)
	age = db.Column(db.Integer)
	sex = db.Column(db.String(5), default='other')
	country = db.Column(db.String(5))
	profile_img = db.Column(db.String)  # stores the filename string of the img file
	about_me = db.Column(db.Text(250))
	city = db.Column(db.String)
	hash = db.Column(db.String(60),  # stores hashed user password
					 unique=False,
					 nullable=False)

	def __str__(self):
		fingerprint = 'INFO :\n'
		for attr, value in self.__dict__.items():
			if not (attr.startswith('_') or attr.isupper()):  # retrieve only public attributes of User class instance
				fingerprint += f"| {attr} -->\t{value}\n"
		return fingerprint

	def set_defaultImg(self):
		if (type(self.sex) is bool) or (self.sex is None):
			if self.sex:
				self.sex = 'm'
			elif self.sex is None:
				self.sex = 'other'
			else:
				self.sex = 'f'
			self.set_defaultImg()
		else:
			if self.sex != 'other':
				self.profile_img = f'def-{self.sex}-{str(ceil(randint(1, 10) * random()))}.jpg'
			else:
				# create Gravatar instead
				self.profile_img = 'favicon.png'

	def get_imgFile(self, foreign_session=False):
		from app.main.methods import handle_userBin # to avoid circular imports

		if ('def-' in self.profile_img) or (self.profile_img == 'favicon.png'):
			return url_for('static', filename=f'avatar/{self.profile_img}')
		return f'{handle_userBin(self.get_file_address(), single_slash=True, foreign_session=foreign_session)}{self.profile_img}'

	def get_imgCarousel(self, foreign_session=False):
		from app.main.methods import handle_userBin # to avoid circular imports

		carousel = []
		file_bin = handle_userBin(self.get_file_address(), single_slash=True, foreign_session=foreign_session)
		try:
			for f in listdir(f'{handle_userBin(self.get_file_address(), absolute_url=True, foreign_session=foreign_session)}'):
				if not(('U__' in f) or ('O__' in f)):
					carousel.append(f'{file_bin}{f}')
					# carousel.append(url_for('static', filename=f'users/{self.get_file_address()}/{f}'))
			return carousel
		except FileNotFoundError:
			return []

	def create_token(self, expireInSec=(8 * 60)):
		return timedTokenizer(current_app.config['SECRET_KEY'], expireInSec).dumps({'load': self.id}).decode('utf-8')

	def has_permission_to(self, action):
		return True

	def is_acc_locked(self):
		if self.acc_locked:
			flash('This account has been temporarly locked because the system detected a brutal attempt to access it.\nTeampicks has been notified about that.', 'danger')
		return self.acc_locked

	def set_last_active(self):
		self.last_active = datetime.utcnow()

	def get_last_active(self):
		return self.last_active

	def set_file_address(self):
		if not self.file_address:
			self.file_address = token_hex(20)
			fl = False
			while not fl:
				try:
					db.session.commit()
					fl = True
				except IntegrityError:
					db.session.rollback()
					self.file_address = token_hex(20)
					fl = False

	def get_file_address(self):
		return self.file_address


class User(db.Model, UserMixin, USER):
	__tablename__ = 'users'

	sports = db.Column(db.Boolean)  # relationship
	groups = db.relationship('Subscription',
							 foreign_keys=[Subscription.member_id],
							 backref=db.backref('member', lazy='joined'),
							 lazy='dynamic',
							 cascade='all, delete-orphan')
	reservations = db.relationship('Reservation',
								   foreign_keys=[Reservation.by_id],
								   backref=db.backref('made_by', lazy='joined'),
								   # adds <made_by> parameter to Reservation model : gain complete access user object
								   lazy='dynamic',
								   cascade='all, delete-orphan')
	followed = db.relationship('Follow',
							   foreign_keys=[Follow.follower_id],
							   backref=db.backref('follower', lazy='joined'),
							   lazy='dynamic',
							   cascade='all, delete-orphan')
	followers = db.relationship('Follow',
							   foreign_keys=[Follow.following_id],
							   backref=db.backref('followed', lazy='joined'),
							   lazy='dynamic',
							   cascade='all, delete-orphan')

	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		self.set_defaultImg()
		self.set_file_address()

	def __repr__(self):
		return f'User {self.id} <{self.username}>'

	def join_as_admin(self, group):
		role = G_Role.query.filter_by(role='admin').first()
		db.session.add(Subscription(group=group, member=self, role=role))

	def send_bookingReq(self, pub, guests):
		# information comes from form or route
		if pub.is_available_for(int(guests)):
			return pub.cache_bookingReq(booked_by=self, guests=int(guests))
		return None

	def send_joinReq(self, group):  # group comes from query in view func
		pass

	def accept_joinReq(self):
		if self.has_permission_to(action='MANAGE_SUBS'):
			pass

	def follow(self, user):
		if not self.is_following(user):
			db.session.add(Follow(follower=self, followed=user))

	def unfollow(self, user):
		f = self.is_following(user, return_follow=True)
		if f[0]:
			db.session.delete(f[1])

	def is_following(self, user, return_follow=False):
		if user.id is None:	# to prevent uncommited users to be followed by self
			if return_follow:
				return False, None
			return False
		f = self.followed.filter_by(following_id=user.id).first()
		if return_follow:
			return f is not None, f 	# return True if the dynamic query given by followed relathionship returns an item
		return f is not None

	def is_followed_by(self, user, return_follow=False):
		if user.id is None:	#to prevent uncommited users to follow self
			if return_follow:
				return False, None
			return False
		f = self.followers.filter_by(follower_id=user.id).first()
		if return_follow:
			return f is not None, f  # return True if the dynamic query given by followers relathionship returns an item
		return f is not None


class Owner(db.Model, UserMixin, USER):
	__tablename__ = 'owners'

	subs_type = db.Column(db.String,
						 nullable=False,
						 default=00)  # stores bin codes whose refers to different acc-subscriptions
	subsExpirationDate = db.Column(db.DateTime, default=None)
	pub = db.relationship('Pub',
						  uselist=False,  # force a one-to-one relationship between owner and his pub
						  backref='owner',
						  cascade='all, delete-orphan')

	def __init__(self, **kwargs):
		super(Owner, self).__init__(**kwargs)
		if self.member_since is None:
			self.member_since = datetime.utcnow()
		self.set_defaultImg()
		self.set_file_address()

	def __repr__(self):
		return f'Owner {self.id} <{self.username}>'

	def associate_pub(self, pub):  # pub object comes from form submission
		self.pub = pub
		self.evaluate_subs()

	def evaluate_subs(self):
		self.evaluate_expirationDate()
		try:
			if self.subs_type != '00':
				self.pub.bookable = True
		except AttributeError:
			pass

	def evaluate_expirationDate(self):
		if self.subsExpirationDate is None:
			self.subsExpirationDate = self.member_since + timedelta(weeks=4)
		elif self.subsExpirationDate <= datetime.utcnow():

			from app.main.methods import check_subs_payment

			if check_subs_payment(self):
				self.subsExpirationDate += timedelta(weeks=4)

	def confirm_pub_reservation(self, res_id):
		res = self.pub.reservations.query.get(res_id)
		res.confirmed = True
		self.pub.book_for(res.guests)


class Pub(db.Model):
	__tablename__ = 'pubs'

	id = db.Column(db.Integer, primary_key=True)
	owner_id = db.Column(db.Integer, db.ForeignKey('owners.id'))
	name = db.Column(db.String(50),
					 nullable=False)
	address = db.Column(db.String,
						nullable=False)
	bookable = db.Column(db.Boolean,
						 nullable=False,
						 default=False)
	phone_num = db.Column(db.String(20))
	seats_max = db.Column(db.Integer,
						  nullable=False)
	seats_booked = db.Column(db.Integer,
							 nullable=False,
							 default=0)
	rating = db.Column(db.Integer,
					   nullable=False,
					   default=0)
	description = db.Column(db.Text(500),
							nullable=True,
							default='let your customer know what you do best.')
	reservations = db.relationship('Reservation',
								   foreign_keys=[Reservation.at_id],
								   backref=db.backref('at', lazy='joined'),
								   # adds <at> parameter to Reservation model : gain complete access pub object
								   lazy='dynamic',
								   cascade='all, delete-orphan')
	reviews = db.relationship('Review',
							  backref=db.backref('recipient', lazy='joined'),
							  lazy='dynamic',
							  cascade='all, delete-orphan')

	def get_address(self):
		return self.address

	def get_rating(self, integer=False):
		if integer:
			return floor(self.rating)
		return round(self.rating, 1)

	def get_description(self):
		return self.description

	def set_manually_availability(self, availability):
		self.seats_booked = self.seats_max - int(availability)

	def get_availability(self):
		return self.seats_max - self.seats_booked

	def notify(self, eventType, item=None):
		# here we should notify Owner of the incoming request in order to let him accept it or not
		# item represent notification body object
		if eventType == 'new-booking':
			pass

	def is_available_for(self, guests):
		if self.bookable:
			if self.get_availability() >= guests:
				return True
		return False

	def cache_bookingReq(self, booked_by, guests):
		tempRes = Reservation(made_by=booked_by,
							at=self,
							guests=guests)
		db.session.add(tempRes)
		self.notify(eventType='new-booking', item=tempRes)
		return tempRes

	def book_for(self, guests):
		self.seats_booked += guests

	def compute_rating(self, return_rating=False):
		rev = Review.query.filter_by(pub_id=self.id).all()
		if len(rev) > 0:
			self.rating = 0
			for r in rev:
				self.rating += r.rating
			self.rating = self.rating/len(rev)
			db.session.commit()
		if return_rating:
			return self.get_rating(integer=True)


class Group(db.Model):
	__tablename__ = 'groups'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(15),
					 unique=True,
					 nullable=False)
	creation_date = db.Column(db.DateTime, default=datetime.utcnow())  # creation date timestamp
	subs = db.relationship('Subscription',
						foreign_keys=[Subscription.group_id],
						backref=db.backref('group', lazy='joined'),
						lazy='dynamic',
						cascade='all, delete-orphan')  # relationship thought group-subs association table
# watchlist = db.Column(db.Boolean)  # stores list of matches the group want to see this week


class G_PERMISSIONS:
	def __init__(self):
		self.POST = 1
		self.MODIFY = 2  # modify group topic and image
		self.MODERATE = 4  # moderate member contents
		self.SET_FLAGS = 8  # flag the group as 'accepting pub offers'
		self.MANAGE_SUBS = 16  # add/remove members

	def admin(self):
		ADMIN = 0
		for a, v in self.__dict__.items():
			if a.isupper():
				ADMIN += v
		return ADMIN

	def member(self):
		return self.POST

	def moderator(self):
		return self.member() + self.MODERATE + self.MODIFY

	def manager(self):
		return self.member() + self.SET_FLAGS + self.MANAGE_SUBS


class G_Role(db.Model):
	__tablename__ = 'group_roles'

	id = db.Column(db.Integer, primary_key=True)
	role = db.Column(db.String, unique=True)
	is_default = db.Column(db.Boolean, default=False, index=True)
	permissions = db.Column(db.Integer, default=0)
	users = db.relationship('Subscription',
							foreign_keys=[Subscription.role_id],
							backref=db.backref('role', lazy='joined')
							)

	def __init__(self, **kwargs):
		super(G_Role, self).__init__(**kwargs)
		if self.permissions is None:
			self.reset_permission()

	def add_permission(self, permission):
		self.permissions += permission

	def remove_permission(self, permission):
		self.permissions -= permission

	def reset_permission(self):
		self.permissions = 0


class Match(db.Model):
	__tablename__ = 'matches'

	id = db.Column(db.Integer, primary_key=True)
	type = db.Column(db.Binary,
					 nullable=False)
	date = db.Column(db.DateTime)
	opponents = db.Column(db.String,
						  nullable=False)  # stores the two teams who will play against each other
