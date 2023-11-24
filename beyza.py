# Kütüphaneler
from pdfminer.high_level import extract_text
import re
from tensorflow.keras.models import load_model
import pickle
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pandas as pd

class PdfParser:
    def __init__(self, model_path="gelismis5.h5", label_encoder_path='label_encoder5.pkl', input_length_path='input_length5.pkl'):

        
        # Modeli ve Parametreleri Yükle
        self.model = load_model(model_path)
        with open(label_encoder_path, 'rb') as f:
            self.le = pickle.load(f)
        with open(input_length_path, 'rb') as f:
            self.input_length = pickle.load(f)
        
    # Tahmin Fonksiyonu
    def hesapla(self, input_text):
        original_length = len(input_text)
        input_text_padded = pad_sequences([[ord(ch) for ch in input_text]], padding='post', maxlen=self.input_length)
        predictions = self.model.predict(input_text_padded, verbose=0)
        predicted_labels = np.argmax(predictions, axis=-1)[0]
        predicted_labels = self.le.inverse_transform(predicted_labels)[:original_length]
        extracted_label = "".join([input_text[i] for i, label in enumerate(predicted_labels) if label != 'O'])
        return extracted_label
    
    # HAGB
    def parse_hukmun_data(self, huk): 
        hagb =["HÜKMÜN AÇIKLANMASININ GERİ BIRAKILMASI (GENEL)","ÇOCUK SUÇU HÜKMÜN AÇIKLANMASININ GERİ  BIRAKILMASI (GENEL)"]
        date_pattern1 = re.compile(r'(\d{2}[/.]\d{2}[/.]\d{2,4})')
        
        tarihler = date_pattern1.findall(huk)
        
        sucTarihi = tarihler[0] if len(tarihler) > 0 else None#
        
        ktarihi = tarihler[1] if len(tarihler) > 1 else None#
        
        kesinlesme = tarihler[2] if len(tarihler) > 2 else None#
      
        # İlk pattern
        pattern = r'\d{4}/\d{1,7} \d{4}/\d{1,7}'
        # Düzenli ifadeyi güncelleyelim
        updated_pattern = re.compile(r"(\d{4}/\d+\s\d{4}/\d+|\d{4}/\d+\s\d{3,4})")

        # İlk pattern ile deneyelim
        found = re.findall(pattern, huk)

        # Eğer bulunamazsa, güncellenmiş pattern ile deneyelim
        if not found:
            found = updated_pattern.findall(huk)

        if found:
            esayisi = found[0].split()[0]
            ksayisi = found[0].split()[1]
    
        while huk and not huk[-1].isdigit():
            huk = huk[:-1]
        colon_position = huk.find(":")

        sira= huk[:colon_position+1] if colon_position != -1 else huk#
        kod= huk.split()[3]#

        kalan = huk.replace(sira, "").replace(kod, "").replace(sucTarihi, "").replace(ksayisi, "").replace(esayisi, "").strip()
        for tarih in tarihler:
            kalan = kalan.replace(tarih, "").strip()
        
        mahkeme = self.hesapla(kalan)
        # print(mahkeme)
        bolme=kalan.split(mahkeme)
        # print(bolme)
        for i in bolme:
            for b in hagb:
                if b in i:
                    karar=b
        # print(karar)            
        kalan= kalan.replace(mahkeme,"").replace(karar,"")
        hukum= None if not kalan.strip() else kalan
        son = {
        # "ham": huk,
        'sira': sira,
        'kod': kod,
        'suctarihi': sucTarihi,    
        'mahkeme': mahkeme,   
        'hukum': hukum,
        'karar':karar,
        'ktarihi': ktarihi,
        'esayisi': esayisi,
        'ksayisi': ksayisi,        
        'kesinlesme': kesinlesme   
    }
        return son
 

    # ERTELEME
    def parse_erteleme_data(self, ertele):
        # Aynı fonksiyonun içeriğini buraya kopyalayarak kullanabilirsiniz

    
        def remove_repeated(text):
            parts = text.split()    
            i = 0
            while i < len(parts):
                part = parts[i]
                if part in parts[i+1:]:
                    # Eşleşme bulunursa, eşleşen parça ve sonrasındaki tüm parçaları sil
                    index_of_repeat = parts[i+1:].index(part) + i + 1
                    del parts[:index_of_repeat]
                    break
                i += 1
            return ' '.join(parts)

        def trim_after_erteleme(text):
            return re.sub(r"(ERTELEME).*", r"\1", text).strip()
        

        while ertele and not ertele[-1].isdigit():
            ertele = ertele[:-1]
        colon_position = ertele.find(":")
        sira = ertele[:colon_position+1] if colon_position != -1 else ertele
        kod = ertele.split()[3]

        # Tarihleri yakalamak için regex desenini tekrar oluşturalım
        date_pattern1 = re.compile(r'(\d{2}[/.]\d{2}[/.]\d{2,4})')
        tarihler = date_pattern1.findall(ertele)
        sucTarihi = tarihler[0] if len(tarihler) > 0 else None
        ktarihi = tarihler[-1] if len(tarihler) > 1 else None
        ksayisi = ertele.split()[-1]
        esayisi = ertele.split()[-2]

        kalan = ertele.replace(sira, "").replace("00000000", "").replace(kod, "").replace(" ".join(tarihler[:-1]), "").replace(tarihler[-1], "").replace(ksayisi, "").replace(esayisi, "").strip()
        kalan = remove_repeated(kalan)
        mahkeme = self.hesapla(kalan)    
        kalan = kalan.replace(mahkeme, "")
        karar = trim_after_erteleme(kalan)
        son = {
                # "ham": ertele,
                'sira': sira,
                'kod': kod,
                'suctarihi': sucTarihi,    
                'mahkeme': mahkeme,
                'hukum':None, 
                'karar': karar,
                'ktarihi': ktarihi,
                'esayisi': esayisi,
                'ksayisi': ksayisi,   
                'kesinlesme':None  
            }
        return son



    # DENETİM
    def parse_denet_data(self, denet):
        ham = denet
        while denet and not denet[-1].isdigit():
            denet = denet[:-1]
        colon_position = denet.find(":")
        sira = denet[:colon_position+1] if colon_position != -1 else denet
        kod = denet.split()[3]
        
        date_pattern1 = re.compile(r'(\d{2}[/.]\d{2}[/.]\d{2,4})')
        tarihler = date_pattern1.findall(denet)
        sucTarihi = tarihler[0] if len(tarihler) > 0 else None
        ktarihi = tarihler[1] if len(tarihler) > 1 else None
        kesinlesme = tarihler[2] if len(tarihler) > 2 else None

        kalan = denet.replace(sira, "").replace(kod, "").strip()
        for tarih in tarihler:
            kalan = kalan.replace(tarih, "").strip()

        esayisi = kalan.split()[-2]
        ksayisi = kalan.split()[-1]
        kalan = kalan.replace(esayisi, "").replace(ksayisi, "").strip()
        mahkeme = self.hesapla(kalan)
        kalan = kalan.replace(mahkeme, "")

        pattern2 = re.escape(kod) + r"(.+?)" + re.escape(mahkeme)
        match = re.search(pattern2, denet)
        sevkm = match.group(1).strip()

        denet = denet.replace(sira, "").replace(kod, "").replace(esayisi, "").replace(ksayisi, "").replace(mahkeme, "").replace(sevkm, "").strip()
        for tarih in tarihler:
            denet = denet.replace(tarih, "").strip()
        ceza = denet

        son = {
            # "ham": ham,
            'sira': sira,
            'kod': kod,
            'suctarihi': sucTarihi,    
            'mahkeme': mahkeme,   
            'hukum': sevkm,
            'karar': ceza,
            'ktarihi': ktarihi,
            'esayisi': esayisi,
            'ksayisi': ksayisi,        
            'kesinlesme': kesinlesme   
        }
        return son



    # DAE
    def parse_dae_data(self, metin):
        def remove_repeated(text):
            parts = text.split()    
            i = 0
            while i < len(parts):
                part = parts[i]
                if part in parts[i+1:]:
                    # Eşleşme bulunursa, eşleşen parça ve sonrasındaki tüm parçaları sil
                    index_of_repeat = parts[i+1:].index(part) + i + 1
                    del parts[:index_of_repeat]
                    break
                i += 1
            return ' '.join(parts)

        original_metin = metin
        while metin and not metin[-1].isdigit():
            metin = metin[:-1]

        if "SOR.NO" in metin:
            metin = metin.replace("SOR.NO","")

        colon_position = metin.find(":")
        sira = metin[:colon_position+1] if colon_position != -1 else metin
        kod = metin.split()[3]
        metin = metin.replace(sira, "").replace(kod, "")
        date_pattern1 = re.compile(r'(\d{2}[/.]\d{2}[/.]\d{2,4})')
        tarihler = date_pattern1.findall(metin)
        for tarih in tarihler:
            metin = metin.replace(tarih, "").strip()
        if len(tarihler) >= 4:
            kesinlesme = tarihler[-1]
            ktarihi = tarihler[-2]
            suctarihi = ' '.join(tarihler[:-2])
        else:
            suctarihi = tarihler[0] if len(tarihler) > 0 else None
            ktarihi = tarihler[1] if len(tarihler) > 1 else None
            kesinlesme = tarihler[2] if len(tarihler) > 2 else None

        pattern = r'\d{4}/\d+\s+\d{4}/\d+'
        found = re.findall(pattern, metin)

        if found:
            esayisi = found[0].split()[0]
            ksayisi = found[0].split()[1]
        
        metin = metin.replace(ksayisi, "").replace(esayisi, "").strip()

        karar = "KAMU DAVASININ AÇILMASININ ERTELENMESİ"
        metin = metin.replace(karar, "").strip()

        metin = remove_repeated(metin)
        mahkeme = self.hesapla(metin)
        hukum = metin.replace(mahkeme, "").strip()
        son = {
            # "ham": original_metin,
            'sira': sira,
            'kod': kod,
            'suctarihi': suctarihi,
            'mahkeme': mahkeme,
            'hukum': hukum,
            'karar': karar,
            'ktarihi': ktarihi,
            'esayisi': esayisi,
            'ksayisi': ksayisi,        
            'kesinlesme': kesinlesme,
            
            
        }
        return son


    # GENEL
    def parse_genel_data(self, metin):
        while metin and not metin[-1].isdigit():
            metin = metin[:-1]
    
        colon_position = metin.find(":")
        sira = metin[:colon_position+1] if colon_position != -1 else metin #1
        kod = metin.split()[3]                                             #2
        date_pattern1 = re.compile(r'(\d{2}[/.]\d{2}[/.]\d{2,4})')
        tarihler = date_pattern1.findall(metin)
        
        if len(tarihler) >= 4:
            kesinlesme = tarihler[-1]                                   #5
            ktarihi = tarihler[-2]                                      #4
            suctarihi = ' '.join(tarihler[:-2])                         #3
        elif len(tarihler) == 3:
            suctarihi = tarihler[0]                                     #3
            ktarihi = tarihler[1]                                       #4
            kesinlesme = tarihler[2]                                    #5
        
        esayisi = metin.split()[-3]                                     #6
        ksayisi = metin.split()[-2]                                     #7

        # Kalan kısmı elde etmek için sonuçtan önceden bulduğunuz değerleri çıkartın
        kalan = metin.replace(sira, "").replace(kod, "").replace(suctarihi, "").replace(ktarihi, "").replace(kesinlesme, "").replace(ksayisi, "").replace(esayisi, "").strip()
        mahkeme = self.hesapla(kalan)                                     #8
        sevkM = re.split(mahkeme, kalan)[0]                               #9
        ceza = re.split(mahkeme, kalan)[1]                                #10

            # Değişkenleri bir sözlükte saklayıp listeye ekliyoruz
        son = {
        'sira': sira,
        'kod': kod,
        'suctarihi': suctarihi,
        'mahkeme': mahkeme, 
        'hukum': sevkM,
        'karar': ceza,
        'ktarihi': ktarihi,
        'esayisi': esayisi,
        'ksayisi': ksayisi,        
        'kesinlesme': kesinlesme   
    }
        return son
    


    # İCM
    def parse_icm_data(self, metin):
        while metin and not metin[-1].isdigit():
            metin = metin[:-1]    
        colon_position = metin.find(":")
        sira = metin[:colon_position+1] if colon_position != -1 else metin                                          #1
        kod = metin.split()[3]
        kalan = metin.replace(sira,"").replace(kod,"").strip()
        date_patterns = r"(\d{2}\.\d{2}\.\d{4}|\d{2}\/\d{2}\/\d{4}|\d{2}\d{2}\d{4})"                                          
        tarihler = re.findall(date_patterns, kalan)    
        kesinlesme = tarihler[2].strip()                                   #5
        ktarihi = tarihler[1].strip()                                      #4
        suctarihi = tarihler[0].strip()                                    #3    
        kalan = kalan.replace(kesinlesme,"").replace(ktarihi,"").replace(suctarihi,"").strip()

        esayisi = kalan.split()[-2]                                    #6
        ksayisi = kalan.split()[-1]
        
        kalan = kalan.replace(esayisi,"").replace(ksayisi,"").strip()

        
        mahkeme = self.hesapla(kalan)                                          #8
        sevkM = re.split(mahkeme, kalan)[0]                               #9
        ceza = re.split(mahkeme, kalan)[1]                                #10 
        son = {
            'sira': sira,
            'kod': kod,
            'suctarihi': suctarihi,
            'mahkeme': mahkeme,
            'hukum': sevkM,
            'karar': ceza,
            'ktarihi': ktarihi,
            'esayisi': esayisi,
            'ksayisi': ksayisi,        
            'kesinlesme': kesinlesme   
        }
        return son

class DataProcessor:    
    def __init__(self, data, reference_date):
        self.df = pd.DataFrame(data) #, columns=['sira', 'kod', 'suctarihi', 'hukum', 'mahkeme', 'karar', 'ktarihi', 'esayisi', 'ksayisi','kesinlesme'])
        self.df = self.df.loc[self.df["kesinlesme"] != "None"]        
        # self.df = self.df.rename(columns={'Sıra': 'sira', 'Kod': 'kod', 'Suç Tarihi': 'suctarihi','Mahkeme': 'mahkeme',
                                        #    'Hüküm': 'hukum',  'Karar': 'karar','K Tarihi': 'ktarihi', 'E Sayısı': 'esayisi', 
                                        #    'K Sayısı': 'ksayisi','Kesinleşme': 'kesinlesme'})
        self.reference_date = pd.Timestamp(reference_date)
        self._process_data()
        self.tekerrur = self._get_tekerrur_data()
        self.sonuc = self._get_result_data()
    
    def _strip_values(self):
        self.df = self.df.map(lambda x: x.strip() if isinstance(x, str) else x)
    
    def _replace_punctuations(self, columns):
        def replacer(val):
            if isinstance(val, str):
                return val.replace('.', '/').replace('-', '/')
            return val
        
        for col in columns:
            self.df[col] = self.df[col].map(replacer)
    
    def _convert_to_date_format(self, columns):
        def converter(val):
            if isinstance(val, str) and len(val) == 8 and val.isdigit():
                return f"{val[:2]}/{val[2:4]}/{val[4:]}"
            return val
        
        for col in columns:
            self.df[col] = self.df[col].map(converter)
    
    def _extract_min_date(self):
        def extractor(value):
            dates = value.split()
            return min([pd.to_datetime(date, dayfirst=True) for date in dates])
        
        mask = self.df["suctarihi"].apply(lambda x: isinstance(x, str) and ' ' in x)
        self.df.loc[mask, 'suctarihi'] = self.df[mask]['suctarihi'].apply(extractor)
    
    def _correct_invalid_dates(self, columns):
        def corrector(val):
            if isinstance(val, str) and val.count('/') == 2:
                day, month, year = val.split('/')
                if day == "00":
                    day = "01"
                if month == "00":
                    month = "01"
                return f"{day}/{month}/{year}"
            return val
        
        for col in columns:
            self.df[col] = self.df[col].apply(corrector)
    
    def _convert_columns_to_datetime(self, columns):
        for col in columns:
            self.df[col] = pd.to_datetime(self.df[col], dayfirst=True, errors='coerce')
    
    def _add_str_date_columns(self, columns):
        for col in columns:
            self.df[f"{col}_str"] = self.df[col].dt.strftime('%d/%m/%Y')
    
    def _get_tekerrur_data(self):        
        result_df = self.df[
            (self.df['kesinlesme'] > self.reference_date) | 
            ((self.df['kesinlesme'].isna()) & (self.df['ktarihi'] > self.reference_date))
        ]
        return result_df[['sira', 'kod', 'suctarihi_str', 'hukum', 'mahkeme', 'karar', 'ktarihi_str', 'esayisi', 'ksayisi', 'kesinlesme_str']]
    
    def _get_result_data(self):
        result_df = self.df[
            (self.df['kesinlesme'].notna()) & 
            (self.df['kesinlesme_son'].notna()) &
            (self.df['kesinlesme'] <= self.reference_date) & 
            (self.df['kesinlesme_son'] >= self.reference_date)
        ]
        return result_df[['sira', 'kod', 'suctarihi_str', 'hukum', 'mahkeme', 'karar', 'ktarihi_str', 'esayisi', 'ksayisi', 'kesinlesme_str']]
    
    def _process_data(self):
        columns_to_replace = ['suctarihi', 'ktarihi', 'kesinlesme']
        
        self._strip_values()
        self._replace_punctuations(columns_to_replace)
        self._convert_to_date_format(columns_to_replace)
        self._extract_min_date()
        self._correct_invalid_dates(columns_to_replace)
        self._convert_columns_to_datetime(columns_to_replace)
        self._add_str_date_columns(columns_to_replace)
        self.df['kesinlesme_son'] = self.df['kesinlesme'] + pd.DateOffset(years=5)
















