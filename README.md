# Monoco
Monoco is a collection of templetes and examples of a relational database's crud functions and models for a B2C service.

# Structure
There's 2 approaches, both coded in python. One is much simpler and uses SQLalchemy. this one can be found in /python-sqlalchemy.
The other one uses PostgreSQL and focuses on cuncurrency. It can be found in /python-concurrrent-postgre.
Both folders will include a file called database.py that creates the .db file andstructures it either as a SQLalchemy one or a PostgreSQL using the official templetes of the respective librairies and the eventual drivers needed.
The models.py will handles the structure and relations of the database and the cre.py will include functions to interact with the data in the database such as parsing a user object from its id or email, creating users, verifying and changing API keys, ecc.


