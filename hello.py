from flask import Flask, render_template, request
from flask import request
import sqlite3
import hashlib
import re

app = Flask(__name__)

DBNAME = "note.db"
id = None
name = None
noteid = None

@app.route('/register',methods=["GET"])
def start():
	title = "PBL Web"
	return render_template("main_in.html", check=0)

@app.route('/register', methods=["POST"])
def register():
	global id, name
	pattern = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
	pass_pattern = "\A(?=.*?[a-z])(?=.*?\d)[a-z\d]{8,100}\Z(?i)"
	id = request.form['id']
	name = request.form['name']
	password = request.form['pass']
	re_pass = request.form['re_pass']
	if not re.match(pattern, id):
		return render_template("main_in.html", check=3)
	if not re.match(pass_pattern, password):
		return render_template("main_in.html", check=4)
	if password != re_pass:
		return render_template("main_in.html", check=2)
	pass_hash = hashlib.sha512(password.encode()).hexdigest()
	conn = sqlite3.connect(DBNAME)
	c = conn.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS user_data(id TEXT PRIMARY KEY, name TEXT, pass_hash TEXT)")
	try:
		c.execute("INSERT INTO user_data VALUES (?,?,?)", (id, name, pass_hash))
	except sqlite3.IntegrityError:
		return render_template("main_in.html", check=1)
	conn.commit()
	c.execute("SELECT * FROM user_data")
	output = c.fetchall()
	conn.close()
	return home()
	


@app.route('/',methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template("login_in.html", check = 0)
	elif request.method == 'POST':
		login_id = request.form['id']
		password = request.form['pass']
		pass_hash = hashlib.sha512(password.encode()).hexdigest()
		conn = sqlite3.connect(DBNAME)
		c = conn.cursor()
		try:
			c.execute("INSERT INTO user_data(id) VALUES (?)", (login_id, ))
		except sqlite3.IntegrityError:
			c.execute("SELECT * FROM user_data")
			output = c.fetchall()
			c.execute("SELECT * FROM user_data WHERE id = (?)", (login_id, ))
			out = c.fetchone()
			global id, name
			db_pass_hash = out[2]
			if pass_hash != db_pass_hash:
				return render_template("login_in.html", check = 1)
			name = out[1]
			id = login_id
			conn.close()
			return home()
		return render_template("login_in.html", check = 1)


@app.route('/home')
def home():
	note_num = []
	mynote_num = 0
	sharenote_num = 0
	conn = sqlite3.connect(DBNAME)
	c = conn.cursor()
	c.execute("SELECT * FROM user_data")
	output = c.fetchall()

	c.execute("SELECT * FROM note_data WHERE account = (?)", (name, ))
	mynote_num = len(c.fetchall())
	c.execute("SELECT * FROM note_data WHERE share = 1 AND account = (?)", (name, ))
	sharenote_num = len(c.fetchall())

	for out in output:
		c.execute("SELECT * FROM note_data WHERE share = 1 AND account = (?)", (out[1], ))
		num = len(c.fetchall())
		note_num.append(num)
	conn.close()
	return render_template("home.html", output=output, id=id, name=name, note_num=note_num, mynote_num=mynote_num, sharenote_num=sharenote_num)


@app.route('/note', methods=['GET','POST'])
def note():
	global noteid, name
	conn = sqlite3.connect(DBNAME)
	c = conn.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS note_data(\
		id INTEGER PRIMARY KEY, \
		title TEXT, \
		massage TEXT, \
		time TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP,'localtime')),\
		account TEXT, \
		share TEXT)")
	if request.method == 'GET':
		noteid = request.args.get('noteid')
		output = [noteid,"",""]
		if noteid == "0" or noteid == "new":
			c.execute("SELECT * FROM note_data WHERE share = 1 ORDER BY time DESC")
			all_out = c.fetchall()
			return render_template("note.html", all_out=all_out, output=output) 
		c.execute("SELECT * FROM note_data WHERE id = (?)", (noteid, ))
		output = c.fetchone()
		c.execute("SELECT * FROM note_data WHERE share = 1 ORDER BY time DESC")
		all_out = c.fetchall()
		conn.close()
		return render_template("note.html", noteid=noteid, output=output, all_out=all_out)
	
	elif request.method == 'POST':
		title = request.form['title']
		massage = request.form['massage']
		share = request.form.get('share')
		c.execute("SELECT * FROM note_data WHERE id = (?)", (noteid, ))
		check_id = c.fetchone()
		if check_id == None:
			c.execute("INSERT INTO note_data(title, massage, account, share) VALUES(?,?,?,?)", (title, massage, name, share))
			conn.commit()
			c.execute("SELECT * FROM note_data ORDER BY id DESC LIMIT 1")
			output = c.fetchone()
			noteid = output[0]
			if share != "1":
				c.execute("SELECT * FROM note_data WHERE account = (?) ORDER BY time DESC", (name, ))
				all_out = c.fetchall()
				conn.close()
				return render_template("mynote.html", all_out=all_out, output=output)
			c.execute("SELECT * FROM note_data WHERE share = 1 ORDER BY time DESC")
			all_out = c.fetchall()
		else:
			c.execute("UPDATE note_data SET {0} = (?), {1} = (?), {2} = (?), {3} = datetime(CURRENT_TIMESTAMP,'localtime') WHERE {4} = (?)".format("title", "massage","share", "time", "id"), (title, massage, share, noteid))
			conn.commit()
			c.execute("SELECT * FROM note_data WHERE id = (?)", (noteid, ))
			output = c.fetchone()
			if share != "1":
				c.execute("SELECT * FROM note_data WHERE account = (?) ORDER BY time DESC", (name, ))
				all_out = c.fetchall()
				conn.close()
				return render_template("mynote.html", all_out=all_out, output=output)
			c.execute("SELECT * FROM note_data WHERE share = 1 ORDER BY time DESC")
			all_out = c.fetchall()
		conn.close()
		return render_template("note.html", all_out=all_out, output=output)

@app.route('/mynote', methods=['GET','POST'])
def mynote():
	global noteid, name
	conn = sqlite3.connect(DBNAME)
	c = conn.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS note_data(\
		id INTEGER PRIMARY KEY, \
		title TEXT, \
		massage TEXT, \
		time TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP,'localtime')),\
		account TEXT, \
		share TEXT)")
	if request.method == 'GET':
		noteid = request.args.get('noteid')
		output = [noteid,"",""]
		if noteid == "0" or noteid == "new":
			c.execute("SELECT * FROM note_data WHERE account = (?) ORDER BY time DESC", (name, ))
			all_out = c.fetchall()
			return render_template("mynote.html", all_out=all_out, output=output) 
		c.execute("SELECT * FROM note_data WHERE id = (?)", (noteid, ))
		output = c.fetchone()
		c.execute("SELECT * FROM note_data WHERE account = (?) ORDER BY time DESC", (name, ))
		all_out = c.fetchall()
		conn.close()
		return render_template("mynote.html", noteid=noteid, output=output, all_out=all_out)
	
	elif request.method == 'POST':
		title = request.form['title']
		massage = request.form['massage']
		share = request.form.get('share')
		c.execute("SELECT * FROM note_data WHERE id = (?)", (noteid, ))
		check_id = c.fetchone()
		if check_id == None:
			c.execute("INSERT INTO note_data(title, massage, account, share) VALUES(?,?,?,?)", (title, massage, name, share))
			conn.commit()
			c.execute("SELECT * FROM note_data ORDER BY id DESC LIMIT 1")
			output = c.fetchone()
			noteid = output[0]
			c.execute("SELECT * FROM note_data WHERE account = (?) ORDER BY time DESC", (name, ))
			all_out = c.fetchall()
		else:
			c.execute("UPDATE note_data SET {0} = (?), {1} = (?), {2} = (?), {3} = datetime(CURRENT_TIMESTAMP,'localtime') WHERE {4} = (?)".format("title", "massage","check", "time", "id"), (title, massage, check, noteid))
			conn.commit()
			c.execute("SELECT * FROM note_data WHERE id = (?)", (noteid, ))
			output = c.fetchone()
			c.execute("SELECT * FROM note_data WHERE account = (?) ORDER BY time DESC", (name, ))
			all_out = c.fetchall()
		conn.close()
		return render_template("mynote.html", all_out=all_out, output=output)



@app.route('/note_delete', methods=["GET","POST"])
def note_delete():
	if request.method == "GET":	
		global noteid, name
		query = request.args.get('q')
		conn = sqlite3.connect(DBNAME)
		c = conn.cursor()
		c.execute("DELETE FROM note_data WHERE id = (?) AND account = (?)", (noteid, name))
		conn.commit()
		if query == "2":
			c.execute("SELECT * FROM note_data WHERE account = (?) ORDER BY time DESC", (name, ))
			all_out = c.fetchall()
			conn.close()
			output = ["0","",""]
			return render_template("mynote.html", all_out=all_out, output=output)
		c.execute("SELECT * FROM note_data WHERE share = 1 ORDER BY time DESC")
		all_out = c.fetchall()
		conn.close()
		output = ["0","",""]
		return render_template("note.html", all_out=all_out, output=output)


@app.route('/delete', methods=["GET"])
def delete_in():
	return render_template("delete_in.html")


@app.route('/delete', methods=["POST"])
def delete_out():
	global id, name
	password = request.form["pass"]
	pass_hash = hashlib.sha512(password.encode()).hexdigest()
	conn = sqlite3.connect(DBNAME)
	c = conn.cursor()
	c.execute("SELECT * FROM user_data WHERE id = (?)", (id, ))
	out = c.fetchone()
	if pass_hash == out[2]:
		c.execute("DELETE FROM user_data WHERE id = (?)",(id,))
		c.execute("DELETE FROM note_data WHERE account = (?)", (name, ))
		conn.commit()
		conn.close
		return render_template("delete.html")
	else:
		return render_template("delete_in.html", check=1)

#削除関数(未使用)------------------------------------------------------------------

@app.route('/delete_all')
def delete_all():
	conn = sqlite3.connect(DBNAME)
	c = conn.cursor()
	c.execute("delete from user_data where id != (?)", (id,))
	c.execute("SELECT * FROM user_data")
	conn.commit()
	output = c.fetchall()
	conn.close
	return render_template("delete.html", output=output, check=0)

#------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)