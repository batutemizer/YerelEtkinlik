from app import app, db, User

def make_admin(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.is_admin = True
            db.session.commit()
            print(f"{username} kullanıcısı admin yapıldı!")
        else:
            print(f"{username} kullanıcısı bulunamadı!")

if __name__ == "__main__":
    username = input("Admin yapılacak kullanıcı adını girin: ")
    make_admin(username) 