from app import app, db

def init_db():
    with app.app_context():
        # Tüm tabloları oluştur
        db.create_all()
        print("Veritabanı tabloları oluşturuldu!")

if __name__ == "__main__":
    init_db() 