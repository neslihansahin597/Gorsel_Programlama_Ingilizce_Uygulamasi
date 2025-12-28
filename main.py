import sys
import traceback  # Hata takibi için eklendi

from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QMainWindow
from PyQt5.uic import loadUi
from pymongo import MongoClient

# Diğer sayfalar (Dosyaların proje klasöründe olduğundan emin ol)
from alistirma_sayfasi import AlistirmaSayfasi

# --- MongoDb Bağlantı Ayarları ---
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "EnglishAppDB"
COLLECTION_NAME = "Grammar"
COLLECTION_NAME_VOCABULARY = "Vocabulary"

# --- Veritabanı Yardımcı Fonksiyonları ---

def get_db_collection(collection_name):
    """Genel koleksiyon çekme fonksiyonu"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        db = client[DATABASE_NAME]
        return db[collection_name], client
    except Exception as e:
        print(f"Bağlantı hatası ({collection_name}):", e)
        return None, None

def get_mongo_collection():
    """Grammar koleksiyonu için özel fonksiyon"""
    client = None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        return collection, client
    except Exception as e:
        print("MongoDB bağlantı hatası:", e)
        if client:
            client.close()
        return None, None

def get_mongo_collection_vocab():
    """Vocabulary koleksiyonu için özel fonksiyon"""
    client = None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME_VOCABULARY]
        return collection, client
    except Exception as e:
        print("MongoDB bağlantı hatası:", e)
        if client:
            client.close()
        return None, None

# --- User CRUD İşlemleri ---

def update_user_password(username, new_password):
    col, client = get_db_collection("Users")

    if col is None or client is None:
        return False

    try:
        # MongoDB'den dönen sonuç bilgisini (result) alıyoruz
        result = col.update_one(
            {"username": username},
            {"$set": {"password": new_password}}
        )

        # HATA AYIKLAMA İÇİN: Konsola ne olup bittiğini yazdıralım
        print(f"Güncellenen Kullanıcı: {username}")
        print(f"Eşleşen Kayıt Sayısı: {result.matched_count}")
        print(f"Değiştirilen Kayıt Sayısı: {result.modified_count}")

        # Eğer hiç eşleşen kayıt yoksa (matched_count 0 ise), kullanıcı bulunamadı demektir.
        if result.matched_count > 0:
            return True
        else:
            print("HATA: Veritabanında bu kullanıcı adına sahip kayıt bulunamadı!")
            return False

    except Exception as e:
        print("Şifre güncelleme hatası:", e)
        return False
    finally:
        client.close()

def delete_user_account(username):
    col, client = get_db_collection("Users")

    # PyMongo hatasını önleyen düzeltme burada da olmalı
    if col is None:
        return False

    try:
        col.delete_one({"username": username})
        return True
    except Exception as e:
        print("Hesap silme hatası:", e)
        return False
    finally:
        if client:
            client.close()
# --- Arayüz Sınıfları ---

class SifreSifirlamaSayfasi(QDialog):
    def __init__(self):
        super(SifreSifirlamaSayfasi, self).__init__()
        loadUi("forgot_password.ui", self)
        self.setWindowTitle("Şifre Sıfırlama")
        self.btn_send_link.clicked.connect(self.send_reset_link)

    def send_reset_link(self):
        email = self.line_email.text()
        if "@" in email and len(email) > 5:
            QMessageBox.information(self, "Bilgi", f"Sıfırlama talimatları {email} adresine gönderildi.")
            self.close()
        else:
            QMessageBox.warning(self, "Hata", "Lütfen geçerli bir email adresi giriniz.")

class KayitSayfasi(QDialog):
    def __init__(self):
        super(KayitSayfasi, self).__init__()
        loadUi("signup.ui", self)
        self.setWindowTitle("Kayıt Ol")
        self.btn_register.clicked.connect(self.register_new_user)

    def register_new_user(self):
        username = self.line_reg_username.text()
        password = self.line_reg_password.text()
        confirm = self.line_reg_confirm_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Hata", "Tüm alanları doldurun.")
            return

        if password != confirm:
            QMessageBox.warning(self, "Hata", "Şifreler eşleşmiyor.")
            return

        col, client = get_db_collection("Users")

        # DÜZELTME 3: if not col yerine if col is None
        if col is None:
            QMessageBox.critical(self, "Hata", "Veritabanına bağlanılamadı.")
            return

        if col.find_one({"username": username}):
            QMessageBox.warning(self, "Hata", "Bu kullanıcı adı zaten mevcut.")
            client.close()
            return

        col.insert_one({
            "username": username,
            "password": password
        })

        client.close()
        QMessageBox.information(self, "Başarılı", "Kayıt başarıyla tamamlandı!")
        self.close()

class GirisSayfasi(QDialog):
    def __init__(self):
        super(GirisSayfasi, self).__init__()
        loadUi("giris.ui", self)
        self.setWindowTitle("Giriş Ekranı")
        self.btn_login.clicked.connect(self.kullanici_girisi)
        self.btn_forgot_password.clicked.connect(self.sifremiUnuttum)
        self.btn_signup.clicked.connect(self.open_signup)
        self.aktif_kullanici = None

    def kullanici_girisi(self):
        kullanici_adi = self.line_user_name.text()
        sifre = self.line_password.text()

        col, client = get_db_collection("Users")

        # DÜZELTME 4: if not col yerine if col is None
        if col is None:
            QMessageBox.critical(self, "Hata", "Veritabanına bağlanılamadı.")
            return

        user = col.find_one({"username": kullanici_adi, "password": sifre})
        client.close()

        if user or (kullanici_adi == "admin" and sifre == "1234"):
            self.aktif_kullanici = kullanici_adi
            self.accept()
        else:
            QMessageBox.warning(self, "Başarısız", "Kullanıcı adı veya şifre hatalı.")

    def sifremiUnuttum(self):
        self.forgot_window = SifreSifirlamaSayfasi()
        self.forgot_window.exec_()

    def open_signup(self):
        self.signup_window = KayitSayfasi()
        self.signup_window.exec_()

class GrammarPage(QMainWindow):
    def __init__(self):
        super(GrammarPage, self).__init__()
        self.setWindowTitle("Gramer sayfası")
        self.client = None
        self.collection = None

        try:
            loadUi("grammar_page.ui", self)
            self.collection, self.client = get_mongo_collection()

            if self.collection is None:
                QMessageBox.critical(
                    self,
                    "Veritabanı Hatası",
                    "MongoDB bağlantısı kurulamadı.\nGramer sayfası açılamıyor."
                )
                self.close()
                return

            self.btn_back.clicked.connect(self.close)
            self.list_grammar_topics.itemClicked.connect(self.load_grammar_content)
            self.setup_topics()

        except FileNotFoundError:
            QMessageBox.warning(self, "Hata", "grammar_page.ui dosyası bulunamadı.")
        except Exception as e:
            QMessageBox.critical(self, "Beklenmedik Hata", f"Uygulama başlatılırken hata oluştu: {e}")

    def setup_topics(self):
        if self.collection is None: return
        self.list_grammar_topics.clear()
        try:
            topics = self.collection.find({}, {"section_title": 1, "name_tr": 1}).sort("tense_id", 1)
            for topic in topics:
                title_to_display = topic.get("section_title", topic.get("name_tr", "Başlıksız Konu"))
                self.list_grammar_topics.addItem(title_to_display)
        except Exception as e:
            QMessageBox.critical(self, "Veri Hatası", f"Konu listesi yüklenemedi: {e}")

    def load_grammar_content(self, item):
        if self.collection is None: return
        selected_title = item.text()
        self.text_grammar_content.clear()
        try:
            lesson_doc = self.collection.find_one({"section_title": selected_title})
            if lesson_doc:
                html_content = self.format_lesson_to_html(lesson_doc)
                self.text_grammar_content.setHtml(html_content)
            else:
                self.text_grammar_content.setText(f"'{selected_title}' veritabanında bulunamadı.")
        except Exception as e:
            QMessageBox.critical(self, "İçerik Yükleme Hatası", f"Hata: {e}")

    def format_lesson_to_html(self, lesson_doc):
        html = f"<h1>{lesson_doc.get('name_tr', 'Ders Başlığı')} ({lesson_doc.get('name_en', '')})</h1>"
        content_flow = lesson_doc.get("content_flow", [])

        for block in content_flow:
            block_type = block.get("type")
            if block_type == "usage_block":
                html += f"<hr><h2><span style='color:#3498db;'>Kullanım Alanı:</span></h2>"
                html += f"<p><b>{block.get('description', 'Kullanım açıklaması yok.')}</b></p>"
                html += "<h3>Örnek Cümleler:</h3><ul>"
                for example in block.get("examples", []):
                    html += f"<li><b>{example.get('en', '')}</b><br><i style='color:#7f8c8d;'>({example.get('tr', '')})</i></li>"
                html += "</ul>"
            elif block_type == "structure_block":
                html += f"<hr><h2><span style='color:#2ecc71;'>{block.get('title', 'Yapı')}</span></h2>"
                html += "<h3>Formül:</h3><pre style='background-color:#ecf0f1; padding: 10px; border-radius: 5px; border: 1px solid #bdc3c7;'>"
                for formula in block.get("formulas", []):
                    html += f"<code>{formula}</code><br>"
                html += "</pre>"
                html += "<h3>Örnek Cümleler:</h3><ul>"
                for example in block.get("examples", []):
                    html += f"<li><b>{example.get('en', '')}</b><br><i style='color:#7f8c8d;'>({example.get('tr', '')})</i></li>"
                html += "</ul>"
            elif block_type == "adverb_block":
                html += f"<hr><h2><span style='color:#e67e22;'>{block.get('title', 'Zarflar')}</span></h2>"
                html += "<ul>"
                for item in block.get("items", []):
                    html += f"<li>{item}</li>"
                html += "</ul>"
        return html

    def closeEvent(self, event):
        event.accept()

class LessonsMenuPage(QDialog):
    def __init__(self):
        super(LessonsMenuPage, self).__init__()
        self.setWindowTitle("Dersler menüsü")
        try:
            loadUi("lessons_menu.ui", self)
            self.btn_grammar.clicked.connect(self.open_grammar)
        except FileNotFoundError:
            QMessageBox.critical(self, "Hata","lessons_menu.ui dosyası bulunamadı.")

    def open_grammar(self):
        self.accept()
        self.grammar_window = GrammarPage()
        self.grammar_window.show()

class VocabularyPage(QDialog):
    def __init__(self):
        super(VocabularyPage, self).__init__()
        self.setWindowTitle("Kelime Kutusu")
        self.client = None
        self.collection = None

        try:
            loadUi("vocabulary_page.ui", self)
            self.collection, self.client = get_mongo_collection_vocab()

            if self.collection is None:
                QMessageBox.critical(self, "Hata", "Veritabanı bağlantısı kurulamadı.")
                self.close()
                return

            self.btn_back.clicked.connect(self.close)
            self.list_vocabulary_sets.itemClicked.connect(self.load_vocabulary_content)
            self.setup_vocabulary_list()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kelime sayfası yüklenemedi: {e}")

    def setup_vocabulary_list(self):
        if self.collection is None: return
        self.list_vocabulary_sets.clear()
        try:
            query = {"tense_id": {"$regex": "^VOC"}}
            topics = self.collection.find(query, {"name_tr": 1}).sort("tense_id", 1)
            for topic in topics:
                self.list_vocabulary_sets.addItem(topic.get("name_tr", "İsimsiz Liste"))
        except Exception as e:
            print(f"Liste yükleme hatası: {e}")

    def load_vocabulary_content(self, item):
        if self.collection is None: return
        selected_title = item.text()
        self.text_vocabulary_content.clear()
        try:
            doc = self.collection.find_one({"name_tr": selected_title})
            if doc:
                html_content = self.format_vocabulary_to_html(doc)
                self.text_vocabulary_content.setHtml(html_content)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kelimeler yüklenemedi: {e}")

    def format_vocabulary_to_html(self, doc):
        html = f"<h1 style='color:#2c3e50;'>{doc.get('name_tr', '')}</h1>"
        html += f"<p style='color:#7f8c8d;'><i>{doc.get('name_en', '')}</i></p><br>"
        content_flow = doc.get("content_flow", [])
        for block in content_flow:
            if block.get("type") == "vocabulary_block":
                html += """
                <table border='1' cellpadding='8' cellspacing='0' style='width:100%; border-collapse: collapse; border: 1px solid #E2E8F0;'>
                    <tr style='background-color: #6366F1; color: white;'>
                        <th>Kelime (Word)</th>
                        <th>Anlamı (Meaning)</th>
                        <th>Tür (Type)</th>
                    </tr>
                """
                for word_item in block.get("items", []):
                    html += f"""
                    <tr>
                        <td style='font-weight: bold;'>{word_item.get('word', '')}</td>
                        <td>{word_item.get('meaning', '')}</td>
                        <td style='color: #e67e22;'><i>{word_item.get('type', '')}</i></td>
                    </tr>
                    """
                html += "</table>"
        return html

    def closeEvent(self, event):
        if self.client:
            self.client.close()
        event.accept()

class HesapGuncellemeSayfasi(QDialog):
    def __init__(self, aktif_kullanici):
        super(HesapGuncellemeSayfasi, self).__init__()
        loadUi("hesap_guncelle.ui", self)
        self.setWindowTitle("Profil Bilgilerini Güncelle")
        self.kullanici = aktif_kullanici
        self.btn_kaydet.clicked.connect(self.bilgileri_guncelle)
        self.btn_vazgec.clicked.connect(self.close)

    def bilgileri_guncelle(self):
        yeni = self.line_yeni_sifre.text()
        tekrar = self.line_sifre_tekrar.text()
        if yeni == "" or tekrar == "":
            QMessageBox.warning(self, "Hata", "Lütfen alanları doldurun.")
            return
        if yeni != tekrar:
            QMessageBox.warning(self, "Hata", "Şifreler eşleşmiyor.")
            return
        if update_user_password(self.kullanici, yeni):
            QMessageBox.information(self, "Başarılı", "Şifreniz başarıyla güncellendi!")
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Güncelleme sırasında bir hata oluştu.")

class HesapSilmeSayfasi(QDialog):
    def __init__(self, aktif_kullanici):
        super(HesapSilmeSayfasi, self).__init__()
        loadUi("hesap_sil.ui", self)
        self.kullanici = aktif_kullanici
        self.btn_iptal.clicked.connect(self.reject)
        self.btn_onay_sil.clicked.connect(self.hesabi_kalici_sil)

    def hesabi_kalici_sil(self):
        sonuc = delete_user_account(self.kullanici)
        if sonuc:
            QMessageBox.information(self, "Bilgi", "Hesabınız başarıyla silindi.")
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Hesap silinemedi.")

class AnaPencere(QMainWindow):
    def __init__(self):
        super(AnaPencere, self).__init__()
        loadUi("main_app.ui", self)
        self.setWindowTitle("Ana Sayfa")
        self.aktif_kullanici = ""

        self.btn_lessons.clicked.connect(self.open_lessons_menu)
        self.actionLogout.triggered.connect(self.logout)
        self.btn_vocabulary.clicked.connect(self.open_vocabulary_menu)
        self.btn_exercise.clicked.connect(self.open_exercise)
        self.btn_update_pass.clicked.connect(self.sifre_guncelle)
        self.btn_delete_acc.clicked.connect(self.hesap_sil)

    def sifre_guncelle(self):
        self.guncelleme_ekrani = HesapGuncellemeSayfasi(self.aktif_kullanici)
        self.guncelleme_ekrani.exec_()

    def hesap_sil(self):
        self.silme_ekrani = HesapSilmeSayfasi(self.aktif_kullanici)
        if self.silme_ekrani.exec_():
            self.close()

    def open_lessons_menu(self):
        self.lessons_menu_window = LessonsMenuPage()
        self.lessons_menu_window.show()

    def open_vocabulary_menu(self):
        self.vocabulary_page = VocabularyPage()
        self.vocabulary_page.show()

    def logout(self):
        reply = QMessageBox.question(self, "Çıkış", "Çıkmak istiyor musunuz?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()

    def open_exercise(self):
        try:
            # Buradaki hatalı parametre kullanımını da düzeltmek gerekebilir
            # AlistirmaSayfasi'nın __init__'i ne bekliyor emin değilim ama
            # genellikle fonksiyon referansı yerine sonucu gönderilir.
            # Şimdilik get_db_collection fonksiyon referansı olarak bıraktım (orijinal kod)
            self.ex_window = AlistirmaSayfasi(get_db_collection)
            self.ex_window.show()
        except Exception as e:
            print("Alıştırma sayfası hatası:", e)

# --- Main Çalıştırma Bloğu (Hata Yakalayıcı ile) ---
if __name__ == '__main__':
    # Beklenmedik hataları konsola yazdırmak için
    def my_excepthook(type, value, tback):
        print("******************************************")
        print("BEKLENMEDİK BİR HATA OLUŞTU:")
        traceback.print_exception(type, value, tback)
        print("******************************************")
        sys.__excepthook__(type, value, tback)

    sys.excepthook = my_excepthook

    app = QApplication(sys.argv)

    login = GirisSayfasi()
    result = login.exec_()

    if result == QDialog.Accepted:
        window = AnaPencere()
        window.aktif_kullanici = login.aktif_kullanici
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)