from FlukeFlute import app, db
from FlukeFlute.utils import add_roles, add_genres, add_languages, create_admin
from FlukeFlute.models import *


if __name__ == "__main__" :

    db.create_all()
    add_roles()
    add_genres()
    add_languages()
    create_admin(username='admin1', email='admin1@gmail.com', password='admin1pass')
    
    app.run(debug=True)

