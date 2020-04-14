import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
 
def main():
   f=open("books.csv")
   b=csv.reader(f)
   for isbn,title,author,year in b:

       if title == 'title':
           continue

       print(isbn,title,author,year)
       db.execute("INSERT INTO book VALUES (:name,:author,:isbn,:year)",
                    {"name":title,"author":author,"isbn": isbn,"year":int(year)})
       print(f"ADDED {title}") 
   db.commit()                

if __name__ == "__main__":
    main()