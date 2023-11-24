import sys
import re
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTableWidget, QTableWidgetItem, QFileDialog, QTableView
from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QHBoxLayout
from PyQt5.QtGui import QFont

from pdfminer.high_level import extract_text
from beyza import PdfParser, DataProcessor

# # Kütüphaneler
# from pdfminer.high_level import extract_text
# import re
# from tensorflow.keras.models import load_model
# import pickle
# import numpy as np
# from tensorflow.keras.preprocessing.sequence import pad_sequences
# import pandas as pd
# # from PyQt5.QtWidgets import QTextEdit

from qt_material import apply_stylesheet  # QtMaterial'i içe aktar


# class ConsoleOutput(QTextEdit):
#     def __init__(self, parent=None):
#         super(ConsoleOutput, self).__init__(parent)
#         self.setReadOnly(True)

#     def write(self, message):
#         self.append(message)

#     def flush(self):
#         pass  # Gerekli bir metot, ama burada bir işlevi yok


# Yazı tipi ayarları
roboto_bold_font = QFont("Roboto", weight=QFont.Bold)
roboto_normal_font = QFont("Roboto")

def al(text):
    lines_pattern = r"(\d+\s+[A-Z]\s+:.+?(?=\d+\s+[A-Z]\s+:|\DÜZENLEYEN|\Z))"
    correct_lines = re.findall(lines_pattern, text, re.DOTALL)
    cleaned_lines = [line.strip() for line in correct_lines]
    return cleaned_lines

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._data.columns[section]
            else:
                return self._data.index[section]
        return None
    
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Adli Sicil V1(beta sürümü)')
        self.resize(960, 480)  # Pencere boyutunu ayarla
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.banned_records = []  # Bu satırı ekleyin

        self.table = None
        self.table_view = None
        self.banned_records_list = None

        self.setup_ui()

    def setup_ui(self):
        self.button = QPushButton('PDF Dosyası Seç')  # self.button olarak tanımla
        # self.button.setStyleSheet("background-color: blue; color: white;")
        # Buton boyutunu ayarla
        # Konsol widget'ını ekleyin
        
        button_width = self.width() // 3
        self.button.setFixedWidth(button_width)
        self.button.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.button)
        # self.console = ConsoleOutput(self)
        # self.layout.addWidget(self.console)
        # # Standart çıktıyı bu yeni widget'a yönlendir
        # sys.stdout = self.console

    def open_file_dialog(self):
        # Mevcut tablo ve liste widgetlarını sıfırla
        if self.table:
            self.layout.removeWidget(self.table)
            self.table.deleteLater()
            self.table = None

        if self.banned_records_list:
            self.layout.removeWidget(self.banned_records_list)
            self.banned_records_list.deleteLater()
            self.banned_records_list = None

        file_name, _ = QFileDialog.getOpenFileName(self, "PDF Dosyası Seçin", "", "PDF Files (*.pdf)")
        if file_name:
            print("Seçilen Dosya:", file_name)
            data, self.banned_records = self.process_pdf(file_name)  # self.banned_records'ı burada güncelleyin
            self.show_data_in_table(data)
            self.add_buttons_to_table()

    def process_pdf(self, file_name):
        # PDF işleme kodunuz (open_file_dialog2 fonksiyonunuzun içeriği)
        # Bu fonksiyon, işlenmiş verileri döndürmelidir.
        # Burada PDF işleme kodunuzu ekleyin
        # Örneğin:
        parser = PdfParser()
        text_pdfminer_one = extract_text(file_name)
        sorguZamani=re.split("\n\nTÜRKİYE CUMHURİYETİ", text_pdfminer_one)[0]
        text_pdfminer = re.sub(r'\n\n\d+/\d+\n\n', '', text_pdfminer_one)
        text = text_pdfminer.replace("\n", " ").replace("   "," ").replace("  "," ").replace(" YUKARIDA KİMLİK BİLGİLERİ BULUNAN KİŞİNİN ADLİ SİCİL ARŞİV KAYDI VARDIR.", "").replace(sorguZamani,"").replace("\x0c", "")
        veriler = al(text)
        hepsi = []
        yasakli_kelimeler = ["ÇOCUK SUÇU ERT", "STGB", "KOŞULLU", "AYNEN İNFAZ","ORTADAN KALDIRMA", "İNFAZIN DURDURULMASI", "KARAR DEĞİŞİKLİĞİ", "DÜŞME"] # "TECİLLİ",
        yasakli_siciller =[] #sayfada daha burayı göstermiyoruz
        for metin in veriler:
            if any(yasakli_kelime in metin for yasakli_kelime in yasakli_kelimeler):
                yasakli_siciller.append(metin)
                continue
            elif "HÜKMÜN" in metin and "ÇOCUK SUÇU" in metin:
                hukmun_cocuk_data = parser.parse_hukmun_data(metin)
                hepsi.append(hukmun_cocuk_data)
            elif "HÜKMÜN" in metin and "DENETİM" in metin: 
                hukmun_denetim_data = parser.parse_hukmun_data(metin)
                hepsi.append(hukmun_denetim_data)
            elif "İCM" in metin and all(word not in metin for word in ["DENETİM", "HÜKMÜN", "ERTELEME", "KAMU"]):
                icm_data = parser.parse_icm_data(metin)
                hepsi.append(icm_data)
            elif "KAMU" in metin and all(word not in metin for word in ["DENETİM", "HÜKMÜN", "ERTELEME", "İCM"]):
                dae_data = parser.parse_dae_data(metin)
                hepsi.append(dae_data)
            elif "HÜKMÜN" in metin and all(word not in metin for word in ["KAMU", "ERTELEME", "DENETİM", "İCM"]):
                hukmun_data = parser.parse_hukmun_data(metin)
                hepsi.append(hukmun_data)
            elif "ERTELEME" in metin and all(word not in metin for word in ["KAMU", "HÜKMÜN", "DENETİM", "İCM"]):
                erteleme_data = parser.parse_erteleme_data(metin)
                hepsi.append(erteleme_data)
            elif "DENETİM" in metin and all(word not in metin for word in ["KAMU", "HÜKMÜN", "ERTELEME", "İCM"]):
                denet_data = parser.parse_denet_data(metin)
                hepsi.append(denet_data)
            else:
                genel_data = parser.parse_genel_data(metin)
                hepsi.append(genel_data)
        # print(yasakli_siciller)
        # return hepsi
        return hepsi, yasakli_siciller

    def show_data_in_table(self, data):
        if not data:
            return

        self.table = QTableWidget(self)
        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(data[0]) + 2)

        headers = list(data[0].keys()) + ["İşlem1", "İşlem2"]
        self.table.setHorizontalHeaderLabels(headers)

        # Sütun başlıkları için kalın Roboto yazı tipini kullan
        for i in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(i)
            header_item.setFont(roboto_bold_font)

        for row_index, row_data in enumerate(data):
            for col_index, key in enumerate(data[0]):
                item = QTableWidgetItem(str(row_data[key]))
                item.setFont(roboto_normal_font)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)  # Hücrenin düzenlenemez olmasını sağla
                self.table.setItem(row_index, col_index, item)


        self.layout.addWidget(self.table)

        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(self.date_edit)


        self.add_row_button = QPushButton('Ekle')
        self.add_row_button.clicked.connect(self.add_empty_row)
        self.layout.addWidget(self.add_row_button)

        show_button = QPushButton("Göster")
        # show_button.setStyleSheet("background-color: blue; color: white;")
        show_button.clicked.connect(self.print_table_data)
        self.layout.addWidget(show_button)
        # Yasaklı Sicil Kayıtları için Açıklama Label'ı
        self.banned_records_label = QLabel("Aşağıda okunamayan siciller gösterilmiştir:")
        self.layout.addWidget(self.banned_records_label)
        # Yasaklı Sicil Kayıtları için List Widget
        self.banned_records_list = QListWidget(self)
        self.layout.addWidget(self.banned_records_list)
         # Yasaklı sicil kayıtlarını listeye ekle
        self.populate_banned_records_list(self.banned_records)

    def add_empty_row(self):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        for col in range(self.table.columnCount() - 2):
            self.table.setItem(row_count, col, QTableWidgetItem(""))
        self.add_buttons_to_row(row_count)

    def add_buttons_to_row(self, row):
        edit_btn = QPushButton('Düzenle')
        del_btn = QPushButton('Sil')

        edit_btn.clicked.connect(lambda _, row=row: self.edit_row(row))
        del_btn.clicked.connect(lambda _, row=row: self.delete_row(row))

        self.table.setCellWidget(row, self.table.columnCount() - 2, del_btn)
        self.table.setCellWidget(row, self.table.columnCount() - 1, edit_btn)

    def add_buttons_to_table(self):
        for row in range(self.table.rowCount()):
            self.add_buttons_to_row(row)       

    def populate_banned_records_list(self, records):
        self.banned_records_list.clear()
        for record in records:
            # Her kayıt için bir satır oluştur
            item_widget = QWidget()
            item_layout = QHBoxLayout()

            label = QLabel(record)
            btn = QPushButton('Sil')
            btn.clicked.connect(lambda _, r=record: self.remove_banned_record(r))

            item_layout.addWidget(label)
            item_layout.addWidget(btn)
            item_layout.addStretch()

            item_widget.setLayout(item_layout)

            # QListWidgetItem oluştur ve widget'ı ekle
            item = QListWidgetItem(self.banned_records_list)
            self.banned_records_list.setItemWidget(item, item_widget)

    def remove_banned_record(self, record):
        # Burada yasaklı sicil kaydını listeden sil
        # Örneğin, yasaklı siciller listesinden kaldır ve listeyi yeniden doldur
        self.banned_records.pop(self.banned_records.index(record))
        self.populate_banned_records_list(self.banned_records)
    
    def delete_row(self, row):
        self.table.removeRow(row)
        self.add_buttons_to_table()  # Satır silindikten sonra butonları yeniden oluştur

    def edit_row(self, row):
        if self.table.item(row, 0).flags() & QtCore.Qt.ItemIsEditable:
            # Kaydetme modu
            for col in range(self.table.columnCount() - 2):
                item = self.table.item(row, col)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.cellWidget(row, self.table.columnCount() - 1).setText('Düzenle')
        else:
            # Düzenleme modu
            for i in range(self.table.rowCount()):
                for col in range(self.table.columnCount() - 2):
                    item = self.table.item(i, col)
                    # Sadece seçili satır düzenlenebilir, diğerleri düzenlenemez
                    if i == row:
                        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                    else:
                        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.cellWidget(row, self.table.columnCount() - 1).setText('Kaydet')
            # self.table.cellWidget(row, self.table.columnCount() - 1).setStyleSheet("background-color: yellow; color: black;")

    def print_table_data(self):
        selected_date = self.date_edit.date().toString("dd/MM/yyyy")

        updated_data = []
        for row in range(self.table.rowCount()):
            row_data = {}
            for col in range(self.table.columnCount() - 2):
                item = self.table.item(row, col)
                if item:
                    row_data[self.table.horizontalHeaderItem(col).text()] = item.text()
                else:
                    row_data[self.table.horizontalHeaderItem(col).text()] = ''
            updated_data.append(row_data)
        processor = DataProcessor(updated_data, reference_date=selected_date)
        processor_results = processor.sonuc.to_dict('records')
        df = pd.DataFrame(processor_results)
        self.show_dataframe(df)

    def show_dataframe(self, df):
        self.table_view = QTableView()
        model = PandasModel(df)
        self.table_view.setModel(model)
        self.table_view.setWindowTitle("Muhtemel Tekerrür içeren siciller")
        self.table_view.resize(800, 600)
        self.table_view.show()



# Uygulama başlatma
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # QtMaterial stilini uygula
    apply_stylesheet(app, theme='light_blue.xml')  # Burada farklı temaları seçebilirsiniz

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())

    # Uygulama başlangıcı

