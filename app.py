import os

from flask import Flask, session,render_template,request, redirect
from flask.ext.session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests #for the external api
import json



from flask import request

app = Flask(__name__)

engine = create_engine(os.getenv("DATABASE_URL")) #DATABASE_URL as been set as a environment variable and its the url of th server database(in postgre)
db = scoped_session(sessionmaker(bind=engine))


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template('index.html', blockhead="aa")

@app.route("/login", methods=["GET","POST"])
def login():
    
    if (request.method == "GET"):
        return render_template("login.html") 
        
    if request.method == "POST":
        username= request.form.get("username")
        password= request.form.get("password")
        data = db.execute("SELECT uname,upass,uid FROM users WHERE uname= '" + username + "' AND upass='"+ password +"';").fetchall()                       
        #'.fetchall()' take all those querry values and stores it in data as a dictionary 
        if len(data) <= 0:
            return render_template("error.html",mess="Username not found")          
        else:
            uid = data[0]['uid']  # data[0]['uid'] means the key of 'uid' from the first row(0th)

            session["uid"] = uid #store the uid value in session ,which is stored in the server, and acts as cookie
            session["user"]= username
            return redirect("/search")
@app.route("/register",methods=["GET","POST"])  
def register():
    
    if (request.method=="GET"):
        return render_template("register.html")
    if (request.method=="POST"):
        username=request.form.get("username")
        password=request.form.get("password")
        data = db.execute("SELECT uname,upass,uid FROM users ").fetchall()                           
        if username in data:
            return render_template("error.html",mess="Username not valid")
        if password in data:
            return render_template("error.html",mess="Password not valid")    
        db.execute("INSERT INTO users(uname, upass) VALUES(:name,:pass)",{"name":username,"pass":password})  
        db.commit()
        return redirect("/login")  

@app.route("/logout")
def logout():
    
    return redirect("/index")


@app.route("/search", methods=["GET","POST"])
def search():

    if request.method == "GET":
        return render_template("search.html")

    if request.method == "POST":
        search= request.form.get("search")
        data=db.execute("SELECT * FROM book WHERE name LIKE :search OR CAST(isbn AS TEXT) LIKE :search OR author LIKE :search OR CAST(year AS TEXT) LIKE :search;",{
            "search": search

        }).fetchall()
        if len(data) <= 0:
            return render_template("error.html",mess="No books found")
        return render_template("result.html",data=data)

@app.route("/review", methods=["GET","POST"])
def review():
    if request.method=="GET":

        isbn = request.args.get('isbn')

        data=db.execute("SELECT * FROM book WHERE isbn=:isbn;",{
            "isbn": isbn
        }).fetchall()
        uid1 = session['uid']
        db_review=db.execute("SELECT rating, review From review WHERE isbn=:isbn AND uid=:uid1;",{
            "isbn": isbn,"uid1": uid1
        }).fetchall()
        count=0
        rev1={}
        rat1={}
        if len(db_review) > 0:
            count+=1
            rev1=db_review[0]['review']
            rat1=db_review[0]['rating']
        data = data[0]

        current_book = {
            "isbn": data.isbn,
            "name": data.name,
            "author": data.author,
            "year": data.year
        }
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": " IHHxdmMDXNtNghRxu1XEw", "isbns": isbn})
        querry=res.json()
        review=querry['books'][0]
        session['current_book'] = current_book

        return render_template("review.html",item=data,review=review,count=count,rev1=rev1,rat1=rat1)

    if request.method == "POST":
        
        uid = session['uid']
        current_book = session['current_book']

        

        review = request.form.get('review') #to get the value of review frm the review.html form
        rating = request.form.get('rating')
    
        db.execute("INSERT INTO review(uid, isbn, rating, review) VALUES (:uid, :isbn, :rating, :review);",{
            "uid": uid,
            "isbn": current_book['isbn'],
            "rating": rating,
            "review": review
        })
        db.commit()

        return(render_template("success.html"))
        


@app.route("/api/<isbn>") 
def api_info(isbn):
    

    query = """ 
        SELECT 
        name AS title,
        author,
        year,
        isbn,
        (SELECT COUNT(*) AS review_count FROM review WHERE isbn = '{0}'),
        (SELECT AVG(rating) AS review_score FROM review WHERE isbn = '{0}')
        FROM book WHERE isbn = '{0}'
    """.format(isbn)
    data = db.execute(query).fetchall()

    
    json_data = []
    for y in data:
        if y['review_score'] == None:
            y['review_score'] = 0
        if y['review_count'] == None:
            y['review_count'] = 0

    for x in data:
        json_data.append({
            "title": x['title'],
            "author": x['author'],
            "year": x['year'],
            "isbn": x['isbn'],
            "review_count": x['review_count'],
            "avgerage_score": float(x['review_score'])
        })


    return json.dumps(json_data)
    




