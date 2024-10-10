import os
import requests
import mysql.connector
import numpy as np
from geopy.distance import geodesic
from dotenv import load_dotenv

load_dotenv()

# Koneksi ke database MySQL
def create_connection():
    return mysql.connector.connect(
        host="localhost",  # Ganti dengan host database Anda
        user="root",       # Ganti dengan username database Anda
        password="",       # Ganti dengan password database Anda
        database=os.getenv("DATABASE")  # Ganti dengan nama database Anda
    )

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paket (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nomor_paket VARCHAR(255),
        pengirim VARCHAR(255),
        penerima VARCHAR(255),
        berat FLOAT,
        alamat_tujuan VARCHAR(255),
        jarak FLOAT,
        internasional BOOLEAN
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# OpenCage API configuration
API_KEY = os.getenv("API_OPEN_CAGE") # Ganti dengan API key dari OpenCage
BASE_URL = "https://api.opencagedata.com/geocode/v1/json"

class Paket:
    def __init__(self, nomor_paket, pengirim, penerima, berat, alamat_tujuan):
        self.nomor_paket = nomor_paket
        self.pengirim = pengirim
        self.penerima = penerima
        self.berat = berat
        self.alamat_tujuan = alamat_tujuan
        self.jarak = self.hitung_jarak(alamat_tujuan)  
        self.internasional = self.cek_internasional(alamat_tujuan)

    def hitung_ongkir(self):
        if self.berat < 5:
            ongkir = 10000 * self.jarak
        elif 5 <= self.berat < 20:
            ongkir = 20000 * self.jarak
        else:
            ongkir = 30000 * self.jarak
        
        if self.internasional:
            ongkir *= 1.5

        return np.floor(ongkir)

    def hitung_jarak(self, alamat_tujuan):
        reference_address = "Yogyakarta, Indonesia"
        ref_coords = get_coordinates(reference_address)
        target_coords = get_coordinates(alamat_tujuan)
        return geodesic(ref_coords, target_coords).kilometers

    def cek_internasional(self, alamat_tujuan):
        negara = get_country(alamat_tujuan)
        return negara.lower() != "indonesia"

    def tampilkan_info(self):
        status = "Internasional" if self.internasional else "Domestik"
        print("================================================")
        print(f"Nomor Paket: {self.nomor_paket}")
        print(f"Pengirim: {self.pengirim}")
        print(f"Penerima: {self.penerima}")
        print(f"Berat: {self.berat} kg")
        print(f"Alamat Tujuan: {self.alamat_tujuan}")
        print(f"Jarak: {self.jarak:.2f} km")
        print(f"Status Pengiriman: {status}")
        print(f"Ongkos Kirim: Rp{self.hitung_ongkir()}")
        print("================================================")

def get_coordinates(address):
    try:
        params = {
            'q': address,
            'key': API_KEY,
            'limit': 1
        }
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raise error jika status bukan 200 OK
        data = response.json()

        if data['results']:
            location = data['results'][0]['geometry']
            return (location['lat'], location['lng'])
        else:
            raise ValueError(f"Alamat '{address}' tidak ditemukan.")
    except Exception as e:
        raise ValueError(f"Error saat mendapatkan koordinat: {e}")

# Menggunakan OpenCage API untuk mendapatkan negara
def get_country(address):
    try:
        params = {
            'q': address,
            'key': API_KEY,
            'limit': 1
        }
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data['results']:
            components = data['results'][0]['components']
            return components.get('country', 'Indonesia')  # Default ke Indonesia jika tidak ada
        else:
            print(f"Negara dari alamat '{address}' tidak ditemukan, diasumsikan sebagai 'Indonesia'")
            return "Indonesia"
    except Exception as e:
        raise ValueError(f"Error saat mendapatkan negara: {e}")

def find_furthest_address_from_db():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT alamat_tujuan FROM paket")
        result = cursor.fetchall()  # Ambil semua alamat dari database
        cursor.close()
        conn.close()

        if not result:
            print("Tidak ada data alamat tujuan di database.")
            return

        # Ambil hanya alamat tujuan dari hasil query
        addresses = [row[0] for row in result]
        reference_address = "Yogyakarta, Indonesia"
        ref_coords = get_coordinates(reference_address)

        furthest_address = None
        max_distance = 0

        # Menghitung jarak untuk setiap alamat tujuan
        for address in addresses:
            try:
                address_coords = get_coordinates(address)
                distance = geodesic(ref_coords, address_coords).kilometers  
                
                if distance > max_distance:
                    max_distance = distance
                    furthest_address = address
            except ValueError as e:
                print(f"Error menghitung jarak untuk alamat '{address}': {e}")

        if furthest_address:
            print(f"Alamat terjauh adalah {furthest_address} dengan jarak {max_distance:.2f} km.")
        else:
            print("Tidak ada alamat yang valid ditemukan untuk menghitung jarak.")
    except mysql.connector.Error as err:
        print(f"Error saat mengambil data dari database: {err}")

def hitung_total_pengiriman_from_db():
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Ambil data ongkir domestik
        cursor.execute("""
        SELECT berat, jarak, internasional FROM paket WHERE internasional = 0
        """)
        paket_domestik = cursor.fetchall()

        # Ambil data ongkir internasional
        cursor.execute("""
        SELECT berat, jarak, internasional FROM paket WHERE internasional = 1
        """)
        paket_internasional = cursor.fetchall()

        cursor.close()
        conn.close()

        # Menghitung total ongkir domestik
        total_domestik = 0
        for berat, jarak, _ in paket_domestik:
            if berat < 5:
                ongkir = 10000 * jarak
            elif 5 <= berat < 20:
                ongkir = 20000 * jarak
            else:
                ongkir = 30000 * jarak
            total_domestik += np.floor(ongkir)

        # Menghitung total ongkir internasional
        total_internasional = 0
        for berat, jarak, _ in paket_internasional:
            if berat < 5:
                ongkir = 10000 * jarak
            elif 5 <= berat < 20:
                ongkir = 20000 * jarak
            else:
                ongkir = 30000 * jarak
            total_internasional += np.floor(ongkir * 1.5)  # Tambahan biaya internasional

        print(f"Total Pengiriman Domestik: Rp{int(total_domestik)}")
        print(f"Total Pengiriman Internasional: Rp{int(total_internasional)}\n")

    except mysql.connector.Error as err:
        print(f"Error: {err}")


def paket_terberat_from_db():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nomor_paket, pengirim, penerima, berat, alamat_tujuan, jarak, internasional FROM paket ORDER BY berat DESC LIMIT 1")
        result = cursor.fetchone()  # Ambil satu data paket dengan berat paling besar
        cursor.close()
        conn.close()

        if result:
            nomor_paket, pengirim, penerima, berat, alamat_tujuan, jarak, internasional = result
            paket_terberat = Paket(nomor_paket, pengirim, penerima, berat, alamat_tujuan)
            paket_terberat.jarak = jarak  # Memperbaiki jarak dari database
            paket_terberat.internasional = bool(internasional)  # Memperbaiki status internasional dari database
            
            print("================================================")
            print("Paket Terberat:")
            paket_terberat.tampilkan_info()
        else:
            print("Tidak ada data paket di database.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")

def menu_admin(paket_list):
    while True:
        print("\n=== MENU ADMIN ===")
        print("1. Masukkan data paket baru")
        print("2. Cek alamat terjauh")
        print("3. Cek paket terberat")
        print("4. Hitung total pengiriman (Domestik dan Internasional)")
        print("5. Keluar")
        
        pilihan = input("Pilih opsi: ")

        if pilihan == "1":
            input_data_paket(paket_list)
        elif pilihan == "2":
            find_furthest_address_from_db()
        elif pilihan == "3":
            paket_terberat_from_db()
        elif pilihan == "4":
            hitung_total_pengiriman_from_db()
        elif pilihan == "5":
            print("Keluar dari sistem.")
            break
        else:
            print("Opsi tidak valid. Silakan coba lagi.")

def input_data_paket(paket_list):
    try:
        nomor_paket = input("Nomor Paket: ")
        pengirim = input("Pengirim: ")
        penerima = input("Penerima: ")
        berat = float(input("Berat (Kg): "))
        alamat_tujuan = input("Alamat Tujuan(alamat, negara): ")

        paket_baru = Paket(nomor_paket, pengirim, penerima, berat, alamat_tujuan)
        paket_baru.tampilkan_info()  # Tampilkan info paket sebagai feedback
        confirm = input("Apakah Anda yakin ingin menyimpan data ini? (y/n): ").lower()

        if confirm == 'y':
            paket_list.append(paket_baru)
            save_to_database(paket_baru)  # Simpan ke database
            print("Data paket berhasil ditambahkan!\n")
        else:
            print("Data paket dibatalkan, tidak disimpan ke database.\n")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}. Data paket tidak disimpan.\n")

def save_to_database(paket):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO paket (nomor_paket, pengirim, penerima, berat, alamat_tujuan, jarak, internasional)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (paket.nomor_paket, paket.pengirim, paket.penerima, paket.berat, paket.alamat_tujuan, paket.jarak, paket.internasional))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise

def main():
    create_table()  # Buat tabel jika belum ada
    paket_list = []  
    print("Sistem Manajemen Pengiriman Paket Perusahaan Logistik Yogyakarta")
    menu_admin(paket_list)

if __name__ == "__main__":
    main()
