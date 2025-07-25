from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel
from flask_mail import Mail  # ✅ make sure this is included

db = SQLAlchemy()
babel = Babel()
mail = Mail()  # ✅ this line is required
