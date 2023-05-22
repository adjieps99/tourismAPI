import json
import psycopg2
import numpy as np
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2
from sklearn.metrics.pairwise import cosine_similarity

# Data dummy destinasi wisata di Jogja
# data = [
#     ['Candi Borobudur', 4.8, -7.607874, 110.203751, 'Candi Budha terbesar di dunia yang memiliki keindahan arsitektur dan pemandangan alam yang menakjubkan.'],
#     ['Keraton Yogyakarta', 4.7, -7.797068, 110.365258, 'Istana kerajaan yang merupakan simbol budaya dan sejarah Kota Yogyakarta.'],
#     ['Pantai Parangtritis', 4.5, -8.006208, 110.315915, 'Pantai yang terkenal dengan legenda Nyi Roro Kidul dan pesona sunset-nya.'],
#     ['Candi Prambanan', 4.6, -7.752020, 110.491895, 'Kompleks candi Hindu terbesar di Indonesia yang menjadi warisan budaya dunia.'],
#     ['Taman Sari', 4.3, -7.809336, 110.362616, 'Kompleks taman dan istana air yang dulunya merupakan tempat rekreasi Sultan Yogyakarta.'],
#     ['Pantai Indrayanti', 4.4, -8.148505, 110.627076, 'Pantai yang menawarkan pasir putih dan air laut yang jernih dengan suasana yang tenang.'],
#     ['Kaliurang', 4.2, -7.594645, 110.432937, 'Kawasan wisata pegunungan yang menawarkan udara segar, pemandangan alam, dan aktivitas pendakian.'],
#     ['Malioboro', 4.7, -7.792605, 110.365800, 'Jalan utama di pusat kota Yogyakarta yang terkenal dengan keramaian, belanja, dan kuliner khas.'],
#     ['Puncak Merapi', 4.5, -7.559595, 110.446409, 'Puncak gunung Merapi yang menawarkan panorama alam yang memukau dan trekking yang menantang.'],
#     ['Candi Ratu Boko', 4.3, -7.790292, 110.474832, 'Candi keraton yang menawarkan pemandangan indah dan keindahan arsitektur pada saat matahari terbenam.'],
#     ['Candi Sambisari', 4.2, -7.785736, 110.397437, 'Candi yang terletak di bawah tanah dengan keindahan arsitektur dan sejarah yang menarik.'],
#     ['Pantai Timang', 4.5, -8.286891, 110.525492, 'Pantai yang terkenal dengan jembatan gantung rakyat yang menantang dan pemandangan laut yang indah.'],
#     ['Hutan Pinus Pengger', 4.3, -7.687751, 110.369285, 'Kawasan hutan pinus yang menawarkan udara segar dan pemandangan yang menenangkan.'],
#     ['Tebing Breksi', 4.6, -7.711931, 110.499754, 'Tebing kapur yang terkenal dengan formasi batuan yang unik dan pemandangan alam yang menakjubkan.'],
#     ['Candi Kalasan', 4.4, -7.809731, 110.471679, 'Candi Buddha yang memiliki keindahan arsitektur dan ornamen relief yang khas.'],
#     ['Goa Jomblang', 4.7, -7.880433, 110.450806, 'Goa alam yang memukau dengan keindahan aliran cahaya dan keunikan stalaktit dan stalagmitnya.'],
#     ['Kampung Gajah', 4.2, -7.813858, 110.410458, 'Wisata keluarga yang menawarkan berbagai wahana seru, taman bermain, dan kebun binatang mini.'],
#     ['Pantai Baron', 4.3, -8.195925, 110.630972, 'Pantai yang menawarkan pesona alam, ombak yang cocok untuk surfing, dan goa-goa kecil yang menarik.'],
#     ['Keraton Kasepuhan', 4.5, -7.032316, 107.909062, 'Keraton yang merupakan salah satu peninggalan kerajaan di Jawa Barat dengan keindahan arsitektur tradisional.'],
#     ['Puncak Becici', 4.4, -7.618862, 110.465895, 'Puncak yang menawarkan pemandangan panorama kota Yogyakarta dan Gunung Merapi yang indah.'],
#     ['Pantai Parangtritis', 4.5, -8.006208, 110.315915, 'Pantai yang terkenal dengan legenda Nyi Roro Kidul dan pesona sunset-nya.'],
#     ['Candi Ratu Boko', 4.4, -7.790292, 110.474832, 'Candi keraton yang menawarkan pemandangan indah dan keindahan arsitektur pada saat matahari terbenam.'],
#     ['Bukit Panguk Kediwung', 4.8, -7.725652, 110.412396, 'Bukit yang menawarkan pemandangan alam yang indah dan suasana yang tenang.'],
#     ['Pantai Glagah', 4.3, -8.087303, 110.445189, 'Pantai yang cocok untuk menikmati keindahan laut, bermain pasir, dan menikmati makanan laut.'],
#     ['Candi Plaosan', 4.5, -7.778759, 110.464189, 'Candi Budha yang memiliki keindahan arsitektur dan nuansa spiritual yang kental.'],
#     ['Puncak Merapi', 4.9, -7.559595, 110.446409, 'Puncak gunung Merapi yang menawarkan panorama alam yang memukau dan trekking yang menantang.'],
#     ['Goa Jomblang', 4.7, -7.880433, 110.450806, 'Goa alam yang memukau dengan keindahan aliran cahaya dan keunikan stalaktit dan stalagmitnya.'],
#     ['Benteng Vredeburg', 4.6, -7.795136, 110.367919, 'Benteng peninggalan kolonial Belanda yang menjadi museum sejarah dan budaya.'],
#     ['Pasar Beringharjo', 4.3, -7.797189, 110.365336, 'Pasar tradisional yang menjual berbagai produk kerajinan dan oleh-oleh khas Yogyakarta.'],
#     ['Museum Affandi', 4.6, -7.779982, 110.379707, 'Museum yang memamerkan karya-karya seni pelukis Affandi dan memiliki taman yang indah.'],
#     ['Kebun Binatang Gembira Loka', 4.1, -7.788375, 110.369741, 'Kebun binatang dengan beragam hewan dan wahana seru untuk dikunjungi oleh keluarga.'],
#     ['Kampung Pelangi', 4.4, -7.790289, 110.376286, 'Kampung dengan rumah-rumah yang dihiasi dengan warna-warni cerah yang indah.'],
#     ['Museum Sonobudoyo', 4.0, -7.797848, 110.365062, 'Museum yang memamerkan koleksi-koleksi benda bersejarah dan kebudayaan Jawa.'],
#     # Tambahkan data dummy lainnya di sini...
# ]

# data = []
# with open('/content/exploreasy-dataset-ready.csv', 'r', newline='') as file:
#     reader = csv.DictReader(file)
#     for row in reader:
#         data.append([
#             row['name'],
#             float(row['rating']) if row['rating'] else 0.0,
#             float(row['latitude']) if row['latitude'] else 0.0,
#             float(row['longitude']) if row['longitude'] else 0.0,
#             row['address'],
#             row['review']
#         ])

# Membuat koneksi ke database
conn = psycopg2.connect(
    host="tiny.db.elephantsql.com",
    port="5432",
    database="kaufzser",
    user="kaufzser",
    password="Z3RIiZHbMzMk_7su0v6dGFm99bvOfkfU"
)

# Membuat kursor
cur = conn.cursor()

# Menjalankan pernyataan SQL untuk mengambil data
cur.execute("SELECT * FROM places")

# Mengambil semua baris hasil query
rows = cur.fetchall()


data = []
for item in rows:
    data.append([
        item[1],
        float(item[5]) if item[5] else 0.0,
        float(item[2]) if item[2] else 0.0,
        float(item[3]) if item[3] else 0.0,
        item[4],
        item[6]
    ])

# print(data)

# Menutup kursor dan koneksi
cur.close()
conn.close()


# Fungsi untuk menghitung jarak antara dua titik koordinat
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius bumi dalam kilometer

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2) * sin(dlat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2) * sin(dlon/2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance


# Fungsi untuk menghitung rekomendasi destinasi
def get_recommendations(user_latitude, user_longitude, data):
    user_position = (user_latitude, user_longitude)

    # Menghitung jarak dari setiap destinasi ke posisi pengguna
    recommendation = []
    for item in data:
        item_lat = item[2]
        item_lon = item[3]
        item_position = (item_lat, item_lon)
        item_rating = float(item[1]) if item[1] else 0.0
        item_distance = calculate_distance(user_latitude, user_longitude, item_lat, item_lon)
        if  item_rating > 4.5 and item_distance <= 10.0:  # Filter rating > 4.0 dan jarak <= 10 km
            item.append(item_distance)
            recommendation.append(item)

    # Mengurutkan data berdasarkan jarak terdekat
    # sorted_data = sorted(recommendation, key=lambda x: x[5])
    sorted_data = sorted(recommendation, key=lambda x: (x[5] is not None, x[5])) if recommendation else []


    return sorted_data[:3]  # Mengambil 3 destinasi terdekat


# Pantai Parangtritis
user_latitude = -8.006208
user_longitude = 110.315915

# # Puncak Merapi
# user_latitude = -7.559595
# user_longitude = 110.446409   

# # Malioboro
# user_latitude = -7.792605
# user_longitude = 110.365800

# # UGM
# user_latitude = -7.7714
# user_longitude = 110.3775

recommendations = get_recommendations(user_latitude, user_longitude, data)

# print(recommendations)

# Menampilkan rekomendasi destinasi dalam format JSON
result = []
for dest in recommendations:
    result.append({
        'nama_destinasi': dest[0],
        'rating': dest[1],
        'latitude': dest[2],
        'longitude': dest[3],
        'address': dest[4],
        'review': dest[5]
    })

# # Mengurutkan data berdasarkan rating secara descending
sorted_data = sorted(result, key=lambda x: x['rating'], reverse=True)

# Mengonversi kembali menjadi JSON
output = json.dumps(sorted_data, indent=4)
print(output)
