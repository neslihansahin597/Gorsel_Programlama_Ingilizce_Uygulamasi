import pandas as pd
import pymongo
import os

# MongoDB Bağlantısını kurduk
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["EnglishAppDB"]
collection = db["Vocabulary"]

# Bu kısımda dosyalar ve seviye eşleşmeleri mevcut
dosya_seviyeleri = {
    "A1.xlsx": "A1",
    "A2.xlsx": "A2",
    "B1.xlsx": "B1",
    "B2.xlsx": "B2",
    "C1.xlsx": "C1"
}


def mongodb_aktarim_yap():
    collection.delete_many({})  #Başlangıcta bir temizleme yaptık.
    print("EnglishAppDB.Vocabulary koleksiyonu temizlendi.")

    for dosya, seviye in dosya_seviyeleri.items():
        if not os.path.exists(dosya):
            print(f"Uyarı: {dosya} bulunamadı, atlanıyor.")
            continue

        try:
            # Excel'i oku
            df = pd.read_excel(dosya).fillna("")
            kelimeler = []

            for _, row in df.iterrows():
                # Sütun isimlerini senin dosyalarındaki ihtimallere göre kontrol etme kısmı
                en = row.get('İngilizce Kelime (Word)') or row.get('İngilizce (Kelime)') or row.get('word', '')
                tr = row.get('Türkçe Anlamı (Meaning)') or row.get('Türkçe (Anlamı)') or row.get('meaning', '')
                tip = row.get('Türü (Type)') or row.get('type', '')

                if en:
                    kelimeler.append({
                        "word": str(en).strip(),
                        "meaning": str(tr).strip(),
                        "type": str(tip).strip()
                    })

            # 50'şerli parçalara böldüğümüz özel kod yapımız
            chunk_size = 50
            for i in range(0, len(kelimeler), chunk_size):
                parca = kelimeler[i: i + chunk_size]
                parca_no = (i // chunk_size) + 1

                #Benim oluşturduğum gramer kısmından bir örnek şema
                dokuman = {
                    "tense_id": f"VOC_{seviye}_PART{parca_no}",
                    "name_en": f"{seviye} Vocabulary Part {parca_no}",
                    "name_tr": f"{seviye} Kelime Listesi Bölüm {parca_no}",
                    "section_title": f"{seviye} Level Words ({i + 1}-{i + len(parca)})",
                    "content_flow": [
                        {
                            "type": "vocabulary_block",
                            "title": f"Kelime Grubu {parca_no}",
                            "items": parca  # Kelime array kısmımız
                        }
                    ]
                }
                collection.insert_one(dokuman)

            print(f"TAMAMLANDI: {seviye} seviyesi için {len(kelimeler)} kelime MongoDB'ye yüklendi.")

        except Exception as e:
            print(f"Hata ({dosya}): {e}")


if __name__ == "__main__":
    mongodb_aktarim_yap()
