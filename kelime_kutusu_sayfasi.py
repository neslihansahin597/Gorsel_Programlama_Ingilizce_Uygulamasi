import pymongo
from PyQt5.QtWidgets import QWidget, QMessageBox, QTextEdit, QTextBrowser
from PyQt5.uic import loadUi


class KelimeKutusuSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            loadUi("KelimeKutusuSayfasi.ui", self)
        except Exception as e:
            print(f"UI Yükleme Hatası: {e}")

        # MongoDB Bağlantı Ayarları
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["EnglishAppDB"]
        self.collection = self.db["Vocabulary"]

        # ListWidget Seviye İsimleri ve Veritabanı Ön eki
        self.seviye_esleme = {
            "A1 Başlangıç": "VOC_A1",
            "A2 Temel": "VOC_A2",
            "B1 Orta": "VOC_B1",
            "B2 Orta Üstü": "VOC_B2",
            "C1 İleri": "VOC_C1"
        }

        # Çıktı kutusunu otomatik bul
        self.output_widget = self.findChild(QTextBrowser, "text_word_content") or self.findChild(QTextEdit,
                                                                                                 "text_word_content")

        if hasattr(self, 'listWidget_seviyeler'):
            self.listWidget_seviyeler.clear()
            self.listWidget_seviyeler.addItems(self.seviye_esleme.keys())
            self.listWidget_seviyeler.itemClicked.connect(self.verileri_mongodbden_getir)

    def verileri_mongodbden_getir(self, item):
        secilen_metin = item.text()
        oneki = self.seviye_esleme.get(secilen_metin)

        if not self.output_widget: return
        self.output_widget.clear()

        try:
            # 1.MongoDB'den ilgili seviyenin tüm parçalarını çek (Regex hepsini bulur)
            sorgu = {"tense_id": {"$regex": f"^{oneki}"}}
            dokumanlar = self.collection.find(sorgu).sort("tense_id", 1)

            html = f"<h2 style='color:#2c3e50;'>{secilen_metin}</h2><hr>"
            html += """
            <table border='1' style='width:100%; border-collapse: collapse; font-family: sans-serif;'>
                <tr style='background-color:#3498db; color:white;'>
                    <th style='padding:10px;'>İngilizce</th>
                    <th style='padding:10px;'>Türkçe</th>
                    <th style='padding:10px;'>Tür</th>
                </tr>
            """

            toplam_kelime = 0
            for dokuman in dokumanlar:
                # 2. Hiyerarşik yapıyı parçala: content_flow -> blocks -> items
                for blok in dokuman.get("content_flow", []):
                    if blok.get("type") == "vocabulary_block":
                        for kelime_obj in blok.get("items", []):
                            en = kelime_obj.get("word", "")
                            tr = kelime_obj.get("meaning", "")
                            tip = kelime_obj.get("type", "")

                            html += f"<tr><td style='padding:5px;'><b>{en}</b></td><td>{tr}</td><td><i>{tip}</i></td></tr>"
                            toplam_kelime += 1

            html += "</table>"

            if toplam_kelime == 0:
                self.output_widget.setHtml("<h3>Bu seviyeye ait veri bulunamadı.</h3>")
            else:
                self.output_widget.setHtml(html)
                print(f"Bilgi: MongoDB'den {toplam_kelime} kelime başarıyla yüklendi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veritabanından okuma yapılamadı: {e}")
