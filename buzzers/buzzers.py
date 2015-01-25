from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
from buzzdata import buzzer, data_for


_VALIDUSERS = 'data/validusers.txt'
_WAITING = 'data/waiting.txt'

webapp = Flask('__name__')


import mysql.connector

conn = mysql.connector.connect(host='127.0.0.1',
								user='root', 
								# Don't forget to change the next two lines, as needed.
								password='itcarlow', 
								database='buzzers', )

cursor = conn.cursor()

def check_logged_in(func):
	""" This decorator function checks to see that a valid user is 
		logged in. If yes, run the called function. If not, send
		the user to the login page. 
	"""
	@wraps(func)
	def wrapped_function(*args, **kwargs):
		if 'logged-in' in session:
			return(func(*args, **kwargs))
		else:
			return render_template( 'nologin.html', 
									title='Authorization Needed',
									nologin=url_for("dologin") )
	return wrapped_function

def checkOKtype(utype):
	""" This (parameterised) decorator makes sure the user can only look at the 
		content that's meant for them (unless they are of type 'admin', in which 
		case they can see EVERYTHING).
	"""
	def check_usertype(func):
		@wraps(func)
		def wrapped_function(*args, **kwargs):
			if session['usertype'] in (utype, 'admin'):
				return(func(*args, **kwargs))
			else:
				return redirect(url_for('indexpage'))
		return wrapped_function
	return check_usertype

@webapp.route('/')
@check_logged_in
def indexpage():
	""" The home page for this webapp. Displays a menu of options
		for the user to choose from.
	"""

	## Another strategy here could be to only display the menu options that are applicable 
	## to the specific user-type logged in. This may result in more logic in the code, or more
	## logic in the templates, which may or may not be advisable/worthwhile. From a UI prespective,
	## it may be better to limit the users options, reducing their frustration at "non-working" 
	## options.

	return render_template("index.html",
						   title="Bahamas Buzzers",
						   logged_in_as=session['userid'],
						   show_logout=True)

@webapp.route('/login', methods=["GET", "POST"])
def dologin():
	""" Either display the login form, or process a filled-in login
		form. Only authorized users can login.
	"""
	def validusertype(u2check, p2check):
		""" Check to see if a user is valid or not, then return a usertype value. 
			If the user is valid, return their type value.
			If the user is invalid, return None. 
		"""
		SQL = """select * from valid_tb"""
		cursor.execute( SQL )
		for row in cursor.fetchall():
			if (u2check== row[0] and p2check == row[1]):
				return row[2]
		return None
	
	if request.method == "GET":
		return render_template("login.html",
							   title='Please login')
	elif request.method == "POST":
		u = request.form['userid']
		p = request.form['passwd']
		_type = validusertype(u, p)
		if _type:
			# Remember state in the session dict.
			session['logged-in'] = True
			session['userid'] = u
			session['passwd'] = p
			session['usertype'] = _type
			return render_template("index.html",
								   title="Bahamas Buzzers",
								   logged_in_as=session['userid'],
								   show_logout=True)
	# Fall though - if nothing above takes, we end up here.
	return redirect(url_for('dologin'))

@webapp.route('/register', methods=["GET", "POST"])
def doregistration():
	""" Perform a registration - display the form, or, process a filled-in
		form by adjusting _WAITING and _VALIDUSERS as needed.
	"""

	def check_in_file(fname, u2check):
		""" Does the identified userid already exist in the file? """
		for row in fname.fetchall():
			if (u2check== row[0]):
				return True
		return False
		
		#with open(fname) as fn:
			#for line in fn:
				#u, p, t = line.strip().split(',')
				#if u2check == u:
					#return True
		# If we get this far, we didn't find the user in the file.
		#return False

	if request.method == "GET":
		return render_template("register.html",
							   title="Registration")
	elif request.method == "POST":
		u = request.form['userid']
		p = request.form['passwd']
		t = request.form['usertype']

		SQL = """select * from valid_tb"""
		cursor.execute( SQL )
		if check_in_file(cursor, u):
			return render_template(
					"register.html",
					title="User {} already registered. Choose another username.".format(u))
		SQL = """select * from waiting_tb"""
		cursor.execute( SQL )
		if check_in_file(cursor, u):
			return render_template(
					"register.html",
					title="User {} waiting. Choose another username.".format(u))
		cursor.execute("""INSERT INTO waiting_tb VALUES(%s,%s,%s)""",(u,p,t))
		conn.commit()
		
		#with open(_WAITING, 'a') as fw:
			#print(u, p, t, sep=',', file=fw)

		return redirect(url_for('dologin'))
	else:
		return redirect(url_for('doregistration'))

@webapp.route('/pilot')
@check_logged_in
@checkOKtype('pilot')
def pilot():
	""" Render the pilot's data.
	"""
	return render_template("display_data.html",
						   title="Data for Pilots",
						   columns=('Destination', 'Times',),
						   data=data_for(buzzer.pilot),
						   show_logout=True)

@webapp.route('/team')
@check_logged_in
@checkOKtype('team')
def team():
	""" Render the departures team's data.
	"""
	return render_template("display_data.html",
						   title="Data for Departures Team",
						   columns=('Time', 'Destination',),
						   data=data_for(buzzer.team),
						   show_logout=True)

@webapp.route('/crew')
@check_logged_in
@checkOKtype('crew')
def crew():
	""" Render the booking crew's data.
	"""
	return render_template("display_data.html",
						   title="Data for Booking Crew",
						   columns=('Destination', 'Time',),
						   data=data_for(buzzer.crew),
						   show_logout=True)

@webapp.route('/admin', methods=["GET", "POST"])
@check_logged_in
@checkOKtype('admin')
def switch_on_users():
	""" The administrator's functionality. Display the list of users waiting
		to be enabled, then let the admin select who to switch on, then (on
		submit) enable the users identified.
	"""
	if request.method == "GET":
		# Grab the data from _WAITING and create a webpage which allows the 
		# administrator to enable users.
		userdata = []
		SQL = """select * from waiting_tb"""
		cursor.execute( SQL )
		for row in cursor.fetchall():
			userdata.append(row)

		if len(userdata) == 0:
			userdata = 'No new users waiting to be enabled.'

		return render_template("admin.html",
							title = "Admin: Enable New Users",
							data=userdata,
							show_logout=True)
	elif request.method == "POST":
		# Switch on those users that have be enabled by the administrator.
		users_to_add = []
		users_not_to_add = []
		# Determine the list of users to enable.
		SQL = """select * from waiting_tb"""
		cursor.execute( SQL )
		for row in cursor.fetchall():
			u = row[0]
			#p = row[1]
			#t = row[2]
			if u in request.form:
				users_to_add.append(row)
			else:
				users_not_to_add.append(row)

		#SQL = """select * from waiting_tb"""
		#cursor.execute( SQL )
		#for line in users_not_to_add:
			#cursor.execute("""INSERT INTO waiting_tb VALUES(%s,%s,%s)""",(u,p,t))
			#conn.commit()
		for line in users_to_add:
			cursor.execute("""INSERT INTO valid_tb VALUES(%s,%s,%s)""",(line[0],line[1],line[2]))
			cursor.execute("""DELETE FROM waiting_tb WHERE name = '%s' """ % line[0])
			conn.commit()
		return redirect(url_for("indexpage"))
	
		#with open(_VALIDUSERS, "a") as fv:
			#for line in users_to_add:
				#print(line, end='', file=fv)
		#return redirect(url_for("indexpage"))
	else:
		return render_template("index.html",
							   title="Bahamas Buzzers",
							   logged_in_as=session['userid'],
							   show_logout=True)

@webapp.route('/logout')
@check_logged_in
def dologout():
	""" Logout a logged-in user, being sure to remove the current user's data 
		from the session dictionary.
	"""
	session.pop('logged-in', None)
	session.pop('userid', None)
	session.pop('passwd', None)
	session.pop('usertype', None)
	return render_template("login.html",
						   title="You are now logged out.")

if __name__ == '__main__':
	webapp.secret_key = b'youwillneverguessmysecretkeyhahahahahahaaaaaaa'
	webapp.run(debug=True, host='0.0.0.0')
