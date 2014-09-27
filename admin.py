from expenses import db, User, hash_password


def create_db():
    db.create_all()


def add_user(email, password):
    db.session.add(User(email=email, password=hash_password(password)))
    db.session.commit()
