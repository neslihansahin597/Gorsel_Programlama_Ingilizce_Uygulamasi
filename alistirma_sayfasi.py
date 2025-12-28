import random
from PyQt5.QtWidgets import QWidget,QMessageBox
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.uic import loadUi


class AlistirmaSayfasi(QWidget):
    #progress_updated = pyqtSignal(int) # İlerlemeyi bildirmek için özel bir sinyal

    def __init__(self, db_helper, main_window=None):
        super().__init__()
        loadUi("alistirma.ui", self) #Arayüzümüzü yükledik
        self.get_db = db_helper #Veritabanı bağlantısına yardımcı olan fonksiyon
        self.main_window = main_window
        # Kolay erişim içn butonları bir liste içine alıyoruz
        self.option_buttons = [self.btn_A, self.btn_B, self.btn_C, self.btn_D]

        # Her butona tıklandığında 'cevap_kontrol' fonksiyonunu çalıştırıyoruz
        for btn in self.option_buttons:
            btn.clicked.connect(self.cevap_kontrol)

        # ComboBox (açılır menü) değiştiğinde kelimeleri yeniden yükle
        self.combo_seviye.currentTextChanged.connect(self.kelimeleri_yukle)
        self.kelimeleri_yukle() # İlk açılışta kelimeleri getir

    def kelimeleri_yukle(self):
        seviye = self.combo_seviye.currentText() # Seçilen seviyeyi al
        col, client = self.get_db("Vocabulary") #Veritabanına yükle
        self.kelimeler = []

        if col is not None:
            # Veritabanında VOC_ seviyesi ile başlayan kayıtları arama kısmı
            query = {"tense_id": {"$regex": f"^VOC_{seviye}"}}
            cursor = col.find(query)
            for doc in cursor:
                for block in doc.get("content_flow", []):
                    if block.get("type") == "vocabulary_block":
                        self.kelimeler.extend(block.get("items", [])) #Kelimeleri listemize ekle
            if client: client.close()

        if self.kelimeler:
            random.shuffle(self.kelimeler) # Kelimeleri rastgele karıştır
            self.index = 0 # Kaçıncı soruda olduğumuz
            self.solved_questions = 0 # Doğru cevap sayısı
            self.total_questions = len(self.kelimeler)
            self.yeni_soru() #İlk soruyu oluştur
        else:
            self.lbl_soru.setText("Kayıt bulunamadı!")

    def yeni_soru(self):
        if self.index < len(self.kelimeler):
            item = self.kelimeler[self.index]
            self.lbl_soru.setText(item['word']) # Ekrana İngilizce kelimeyi yaz
            self.correct_answer = item['meaning'] # Doğru cevabı değişkene kaydet

            siklar = [self.correct_answer] # Önce doğru cevabı ekle
            # Yanlış şıkları seç (Mevcut kelime dışındaki kelimelerden rastgele 3 tane)
            yanlislar = [k['meaning'] for k in self.kelimeler if k['meaning'] != self.correct_answer]
            siklar.extend(random.sample(yanlislar, min(len(yanlislar), 3)))
            random.shuffle(siklar) # Şıkların yerini karıştırıyoruz hep aynı şık denk gelmesin diye

            # Butonlara metinleri ata ve stilleri sıfırla
            for i, btn in enumerate(self.option_buttons):
                btn.setText(siklar[i])
                btn.setEnabled(True)
                # Varsayılan renk (Beyaz)
                btn.setStyleSheet(
                    "background-color: white; border: 2px solid #6c5ce7; border-radius: 12px; padding: 10px;")
        else:
            self.lbl_soru.setText("Seviye Tamamlandı!")

    def cevap_kontrol(self):
        secilen = self.sender() # Hangi butona basıldığını belirler
        if secilen.text() == self.correct_answer:
            # Doğruysa yeşil yap
            secilen.setStyleSheet("background-color: #2ecc71; color: white; border-radius: 12px;")
            self.solved_questions += 1
        else:
            # Yanlışsa kırmızı yap
            secilen.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 12px;")

        self.index += 1 # Bir sonraki soru indeksine geç
        QTimer.singleShot(1000, self.yeni_soru) #1 saniye bekle yeni soruya gec

