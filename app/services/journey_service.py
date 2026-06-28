from app.models import User, JourneyStepProgress

# Step yang termasuk "bimbingan pranikah" lintas agama — dipakai untuk
# trigger notifikasi pengingat saat step ini terbuka (unlocked).
GUIDANCE_STEP_KEYS = {
    'suscatin_islam',
    'kpp_katolik',
    'katekisasi_protestan',
    # Hindu/Buddha/Konghucu tidak punya sesi "kelas" terpisah dalam data asal
    # (langsung ke upacara), sehingga tidak dimasukkan ke definisi "bimbingan".
}

STEP_DEFINITIONS = [
    # STEP 1: RT/RW (UNIVERSAL)
    {
        'step_key': 'rt_rw',
        'step_order': 1,
        'category': 'Birokrasi Tingkat RT/RW',
        'title': 'Surat Pengantar RT/RW',
        'subtitle': 'Langkah awal administrasi untuk menyatakan domisili pengurusan nikah.',
        'target_institution': 'Ketua RT & RW Setempat',
        'requires_document': True,
        'religion': 'Universal',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': [
            'Fotokopi KTP Calon Pengantin (CPP & CPW)',
            'Fotokopi Kartu Keluarga (KK) terbaru',
            'Surat Pengantar asli dari RT ditandatangani RW',
        ],
        'step_by_step': [
            'Datangi Ketua RT membawa berkas KTP & KK untuk meminta draf surat pengantar.',
            'Bawa draf surat dari RT ke Ketua RW untuk ditandatangani dan dicap resmi.',
            'Simpan surat pengantar RW untuk dibawa ke Kantor Kelurahan.',
        ],
    },

    # STEP 2: KELURAHAN (UNIVERSAL)
    {
        'step_key': 'kelurahan_n1n4',
        'step_order': 2,
        'category': 'Kantor Kelurahan / Desa',
        'title': 'Formulir N1 - N4 Kelurahan',
        'subtitle': 'Pembuatan surat keterangan resmi dari negara berupa berkas Model N1, N2, N3, dan N4.',
        'target_institution': 'Kantor Kelurahan / Balai Desa',
        'requires_document': True,
        'religion': 'Universal',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': [
            'Surat Pengantar RT/RW asli',
            'Fotokopi KTP & KK Mempelai beserta Orang Tua (2 rangkap)',
            'Fotokopi Akta Kelahiran & Ijazah Terakhir',
            'Pas Foto berdampingan 2x3 & 3x4 latar biru (Islam) atau merah (Non-Islam)',
            'Surat Pernyataan Belum Pernah Menikah bermaterai Rp10.000',
            'Akta Cerai / Kematian asli (Jika status Duda/Janda)',
        ],
        'step_by_step': [
            'Serahkan berkas pengantar RT/RW ke loket pelayanan umum Kelurahan.',
            'Petugas akan memverifikasi status lajang/pernikahan sebelumnya.',
            'Tunggu petugas mencetak berkas Model N1 (Ket. Nikah), N2 (Asal-Usul), N3 (Persetujuan Mempelai), dan N4 (Ket. Orang Tua).',
            'Tandatangani berkas bersama lurah/kepala desa.',
        ],
    },

    # STEP 3: KESEHATAN (UNIVERSAL)
    {
        'step_key': 'kesehatan_elsimil',
        'step_order': 3,
        'category': 'Pemeriksaan Medis Catin',
        'title': 'Sertifikat Sehat Puskesmas & Elsimil',
        'subtitle': 'Pemeriksaan laboratorium fisik catin serta pelaporan kesehatan reproduksi pada BKKBN.',
        'target_institution': 'Puskesmas Kecamatan & Aplikasi Elsimil BKKBN',
        'requires_document': True,
        'religion': 'Universal',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': [
            'Fotokopi KTP & KK kedua mempelai',
            'Pas foto ukuran 2x3 (2 lembar)',
            'Hasil cek lab darah (HB, Goldar, Rhesus, HIV, Sifilis, Hepatitis B)',
        ],
        'step_by_step': [
            'Datang ke Puskesmas pagi hari (disarankan puasa 8 jam untuk cek gula darah).',
            'Lakukan pemeriksaan sampel darah, urine, dan suntik Vaksin Tetanus Toksoid (TT) bagi wanita.',
            'Unduh aplikasi Elsimil di Google Play / App Store.',
            'Isi kuesioner Elsimil dan masukkan angka hasil cek lab darah Puskesmas.',
            'Unduh Sertifikat Elsimil berupa QR Code jika hasil dinyatakan ideal/siap nikah.',
        ],
    },

    # STEP REKOMENDASI: BEDA KOTA / PROVINSI (NUMPANG NIKAH)
    {
        'step_key': 'numpang_nikah',
        'step_order': 4,
        'category': 'Dispensasi Khusus Regional',
        'title': 'Surat Rekomendasi Numpang Nikah',
        'subtitle': 'Diperlukan karena lokasi akad/pemberkatan diselenggarakan di luar wilayah KTP asal Anda.',
        'target_institution': 'KUA Asal KTP / Disdukcapil Asal KTP',
        'requires_document': True,
        'religion': 'Universal',
        'target_gender': 'Universal',
        'is_for_out_of_town': True,
        'is_for_foreigner': False,
        'requirements': [
            'Berkas N1 - N4 asli dari kelurahan asal',
            'Fotokopi KTP & KK kedua mempelai',
            'Surat pengantar rekomendasi dari kelurahan asal',
        ],
        'step_by_step': [
            'Setelah berkas N1-N4 terbit di Kelurahan asal, minta surat pengantar numpang nikah.',
            'Bawa berkas tersebut ke KUA asal (untuk Islam) atau Disdukcapil asal (untuk Non-Islam).',
            'Sampaikan kota dan kecamatan tujuan pernikahan (contoh: KUA Kec. Gubeng, Kota Surabaya).',
            'Petugas akan menerbitkan lembar Surat Rekomendasi Nikah resmi.',
        ],
    },

    # STEP WNA 1: KEDUTAAN
    {
        'step_key': 'cni_kedutaan',
        'step_order': 5,
        'category': 'Legalitas Internasional Pasangan',
        'title': 'Certificate of No Impediment (CNI)',
        'subtitle': 'Surat keterangan dari negara asal WNA yang menyatakan bahwa dia sah & lajang untuk menikah.',
        'target_institution': 'Kedutaan Besar / Konsulat Negara Asal WNA di Indonesia',
        'requires_document': True,
        'religion': 'Universal',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': True,
        'requirements': [
            'Paspor asli WNA yang masih berlaku',
            'Akta Kelahiran WNA (Terjemahan Tersumpah bahasa Indonesia/Inggris)',
            'Surat Keterangan Status Lajang resmi dari negara asal WNA',
            'Surat Keterangan Domisili / Cap Izin Tinggal Visa Turis',
        ],
        'step_by_step': [
            'Pasangan WNA harus membuat janji temu dengan kedutaan besarnya di Jakarta.',
            'Serahkan seluruh berkas bukti lajang dari negara asal ke konsuler.',
            'Bayar biaya administrasi penerbitan surat izin menikah internasional.',
            'Tunggu dokumen CNI berbahasa Indonesia/Inggris diterbitkan dan dicap oleh Kedutaan.',
        ],
    },

    # STEP WNA 2: IMIGRASI & NOTARIS
    {
        'step_key': 'imigrasi_notaris',
        'step_order': 6,
        'category': 'Administrasi Imigrasi & Hukum RI',
        'title': 'Izin Imigrasi, Kepolisian & Perjanjian Perkawinan',
        'subtitle': 'Persiapan perlindungan aset tanah WNI (Prenup) dan surat izin kepolisian untuk WNA.',
        'target_institution': 'Kantor Notaris & Kepolisian Negara Republik Indonesia (Polres)',
        'requires_document': True,
        'religion': 'Universal',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': True,
        'requirements': [
            'Paspor & KITAS/KITAP Pasangan WNA (jika menetap)',
            'Surat Keterangan Lapor Diri (SKLD) dari Polres setempat',
            'Draf Akta Perjanjian Perkawinan (Prenuptial Agreement) dari Notaris',
            'Surat Keterangan Mualaf (Khusus jika WNA masuk Islam)',
        ],
        'step_by_step': [
            'Laporkan keberadaan WNA ke Polres setempat untuk mendapatkan Surat Keterangan Lapor Diri.',
            'Sangat Wajib: Datangi Notaris sebelum hari H pernikahan untuk membuat Perjanjian Pisah Harta (Prenup).',
            'Jika tidak membuat Prenup, hak milik tanah SHM pihak WNI akan hangus demi hukum pasca menikah dengan WNA.',
            'Dapatkan salinan Akta Notaris Perjanjian Perkawinan untuk didaftarkan ke KUA/Disdukcapil.',
        ],
    },

    # JALUR ISLAM: KUA
    {
        'step_key': 'kua_daftar_nikah',
        'step_order': 7,
        'category': 'Kementerian Agama (Islam)',
        'title': 'Pendaftaran Kehendak Nikah di KUA',
        'subtitle': 'Verifikasi akhir dokumen, penentuan wali, dan pembayaran biaya nikah negara.',
        'target_institution': 'KUA Kecamatan Lokasi Pernikahan',
        'requires_document': True,
        'religion': 'Islam',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': [
            'Seluruh berkas N1 - N4 dari Kelurahan',
            'Surat Rekomendasi Nikah (Jika beda kecamatan/kota)',
            'Sertifikat Kesehatan Puskesmas & QR Code Elsimil',
            'Fotokopi KTP 2 orang saksi nikah laki-laki',
            'Fotokopi KTP Wali Nikah & Kartu Keluarga Wali',
            'Bukti bayar PNBP Rp600.000 via Bank (Jika akad di luar jam/kantor KUA)',
            'Akta Perjanjian Kawinan dari Notaris (Jika ada pasangan WNA)',
        ],
        'step_by_step': [
            'Daftar online terlebih dahulu di situs SIMKAH Kemenag atau datang langsung ke KUA.',
            'Serahkan seluruh berkas fisik paling lambat 10 hari kerja sebelum tanggal akad nikah.',
            'Lakukan pemeriksaan berkas bersama penghulu untuk pencocokan maskawin dan keabsahan wali.',
            'Jika menikah di luar kantor KUA atau hari libur, ambil kode billing bank dan bayar Rp600.000 ke Bank Persepsi.',
        ],
    },
    {
        'step_key': 'suscatin_islam',
        'step_order': 8,
        'category': 'Bimbingan Pranikah KUA',
        'title': 'Kursus Calon Pengantin (Suscatin)',
        'subtitle': 'Mengikuti kelas pembekalan keluarga sakinah oleh penasihat BP4 KUA.',
        'target_institution': 'Kantor KUA Kecamatan',
        'requires_document': True,
        'religion': 'Islam',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': ['Kartu bimbingan mandiri Suscatin dari KUA'],
        'step_by_step': [
            'Hadir bersama pasangan di KUA sesuai jadwal pembekalan pranikah yang ditentukan.',
            'Ikuti materi bimbingan reproduksi, manajemen konflik, dan hukum waris keluarga selama 1-2 hari.',
            'Terima Sertifikat Suscatin resmi sebagai syarat sah buku nikah dicetak.',
        ],
    },

    # JALUR KATOLIK
    {
        'step_key': 'kpp_katolik',
        'step_order': 7,
        'category': 'Sakramen Pernikahan Gereja',
        'title': 'Kursus Pranikah & Penyelidikan Kanonik',
        'subtitle': 'Bimbingan iman perkawinan Katolik dan ujian kanonik bersama Pastor.',
        'target_institution': 'Gereja Paroki Asal',
        'requires_document': True,
        'religion': 'Katolik',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': [
            'Surat Baptis terbaru (Maksimal 6 bulan terakhir)',
            'Sertifikat Kursus Persiapan Perkawinan (KPP) Gereja',
            'Surat Pengantar Kelurahan (N1-N4)',
        ],
        'step_by_step': [
            'Ikuti Kursus Persiapan Perkawinan (KPP) selama beberapa minggu di Gereja.',
            'Lakukan pendaftaran pengumuman pernikahan di warta jemaat gereja (minimal 3 minggu berturut-turut).',
            'Khusus Katolik: Jalani ujian Penyelidikan Kanonik bersama Pastor paroki untuk memastikan kesucian sakramen.',
        ],
    },

    # JALUR PROTESTAN
    {
        'step_key': 'katekisasi_protestan',
        'step_order': 7,
        'category': 'Sakramen Pernikahan Gereja',
        'title': 'Kursus Pranikah & Pemberkatan Jemaat',
        'subtitle': 'Bimbingan iman perkawinan Kristen Protestan dan pencatatan pengumuman jemaat.',
        'target_institution': 'Gereja Jemaat Asal',
        'requires_document': True,
        'religion': 'Kristen Protestan',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': [
            'Surat Baptis & Surat Sidi asli',
            'Sertifikat Katekisasi/Kursus Pranikah Gereja',
            'Surat Pengantar Kelurahan (N1-N4)',
        ],
        'step_by_step': [
            'Daftarkan kehendak nikah ke sekretariat gereja lokal.',
            'Ikuti kelas bimbingan konseling pernikahan Kristen bersama pendeta.',
            'Pastikan nama Anda dan pasangan diumumkan dalam lembar warta jemaat gereja.',
        ],
    },

    # JALUR HINDU
    {
        'step_key': 'wiwaha_hindu',
        'step_order': 7,
        'category': 'Pemberkatan Agama Hindu',
        'title': 'Upacara Wiwaha Samskara & PHDI',
        'subtitle': 'Ritual pernikahan suci Hindu dan penerbitan piagam nikah PHDI.',
        'target_institution': 'Parisada Hindu Dharma Indonesia (PHDI) setempat',
        'requires_document': True,
        'religion': 'Hindu',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': ['Surat N1-N4', 'Surat Keterangan Sudhi Wadani (jika salah satu masuk Hindu)', 'Saksi upacara'],
        'step_by_step': [
            'Laksanakan prosesi sakral Wiwaha Samskara dipimpin oleh Sulinggih/Pinandita.',
            'Laporkan piagam upacara perkawinan ke kantor PHDI daerah untuk mendapatkan sertifikat legal agama.',
        ],
    },

    # JALUR BUDDHA
    {
        'step_key': 'pemberkatan_buddha',
        'step_order': 7,
        'category': 'Pemberkatan Agama Buddha',
        'title': 'Pemberkatan Perkawinan Pandita Vihara',
        'subtitle': 'Upacara pernikahan Buddhis di depan altar dan pengesahan majelis WALUBI.',
        'target_institution': 'Vihara / Majelis Agama Buddha (WALUBI)',
        'requires_document': True,
        'religion': 'Buddha',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': ['Surat N1-N4 dari Kelurahan', 'Fotokopi KTP Catin & Saksi'],
        'step_by_step': [
            'Lakukan ritual upacara pemberkatan suci di hadapan Pandita/Romo di Vihara.',
            'Minta penandatanganan Surat Keterangan Perkawinan Buddhis dari WALUBI/Majelis terkait.',
        ],
    },

    # JALUR KONGHUCU
    {
        'step_key': 'liyuan_konghucu',
        'step_order': 7,
        'category': 'Pemberkatan Agama Konghucu',
        'title': 'Upacara Li Yuan (Pemberkatan Li Tang)',
        'subtitle': 'Pemberkatan pernikahan suci secara Litang di bawah naungan MATAKIN.',
        'target_institution': 'Kong Miao / Makin (MATAKIN) Setempat',
        'requires_document': True,
        'religion': 'Konghucu',
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': ['Surat N1-N4 Kelurahan', 'Fotokopi KTP & KK'],
        'step_by_step': [
            'Laksanakan rangkaian ritus pernikahan suci Li Yuan di Li Tang / Klenteng Khusus.',
            'Dapatkan Akta Pemberkatan Perkawinan Agama Konghucu dari pengurus MAKIN.',
        ],
    },

    # PENCATATAN SIPIL (NON-ISLAM) — satu definisi, berlaku untuk semua agama non-Islam
    {
        'step_key': 'disdukcapil_sipil',
        'step_order': 8,
        'category': 'Kementerian Dalam Negeri (Sipil)',
        'title': 'Pencatatan Akta Nikah Disdukcapil',
        'subtitle': 'Wajib dilaporkan maksimal 60 hari setelah pemberkatan agama agar pernikahan diakui negara secara hukum perdata.',
        'target_institution': 'Dinas Kependudukan dan Catatan Sipil (Disdukcapil)',
        'requires_document': True,
        'religion': 'NonIslam',  # ditangani khusus di filter, lihat _matches_religion()
        'target_gender': 'Universal',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': [
            'Surat Bukti Pernikahan / Pemberkatan asli dari Gereja/Vihara/PHDI',
            'Berkas asli Model N1 - N4 dari Kelurahan',
            'Fotokopi KTP & KK kedua mempelai dan KTP orang tua',
            'Fotokopi KTP 2 orang saksi pencatatan',
            'Pas foto berdampingan ukuran 4x6 (5 lembar) latar merah',
            'Akta Perjanjian Kawinan Notaris (Jika pasangan WNA)',
        ],
        'step_by_step': [
            'Datang ke Kantor Disdukcapil atau daftar online via aplikasi dukcapil daerah maksimal 60 hari pasca pemberkatan.',
            'Hadirkan 2 orang saksi secara fisik (jika pengurusan offline).',
            'Petugas Catatan Sipil akan menandatangani Buku Registrasi Akta Pernikahan.',
            'Terima lembar Kutipan Akta Perkawinan resmi negara.',
        ],
    },

    # SYARAT TAMBAHAN PEREMPUAN
    {
        'step_key': 'syarat_wanita',
        'step_order': 9,
        'category': 'Syarat Tambahan Mempelai Wanita',
        'title': 'Surat Keterangan Bebas Janda / Persetujuan Wali',
        'subtitle': 'Dokumen pendukung legalitas status perdata khusus mempelai wanita.',
        'target_institution': 'Kelurahan Setempat',
        'requires_document': True,
        'religion': 'Universal',
        'target_gender': 'Perempuan',
        'is_for_out_of_town': False,
        'is_for_foreigner': False,
        'requirements': [
            'Surat pernyataan tertulis belum pernah menikah bermaterai',
            'KTP asli orang tua / wali nikah kandung',
        ],
        'step_by_step': [
            'Lengkapi formulir tambahan di kelurahan yang melampirkan silsilah keluarga.',
            'Pastikan status wali nikah nasab (ayah kandung/saudara laki-laki) sinkron dengan KK.',
        ],
    },
]


def _matches_religion(step_religion: str, user_religion: str) -> bool:
    if step_religion == 'Universal':
        return True
    if step_religion == 'NonIslam':
        return user_religion != 'Islam'
    return step_religion == user_religion


def get_steps_for_user(user: User) -> list[dict]:
    """Filter STEP_DEFINITIONS sesuai profil user, lalu urutkan stepOrder."""
    filtered = [
        s for s in STEP_DEFINITIONS
        if _matches_religion(s['religion'], user.religion)
        and (s['target_gender'] == 'Universal' or s['target_gender'] == user.gender)
        and (not s['is_for_out_of_town'] or user.is_out_of_town)
        and (not s['is_for_foreigner'] or user.is_foreigner)
    ]
    filtered.sort(key=lambda s: s['step_order'])
    return filtered


def merge_with_progress(steps: list[dict], progress_rows: list[JourneyStepProgress]) -> list[dict]:
    """Gabungkan definisi step (statis) dengan progress tersimpan user (dinamis)."""
    progress_map = {p.step_key: p for p in progress_rows}

    merged = []
    for idx, step in enumerate(steps):
        prog = progress_map.get(step['step_key'])
        is_done = prog.is_done if prog else False

        # Step terkunci jika BUKAN step pertama DAN step sebelumnya belum selesai.
        is_locked = False
        if idx > 0:
            prev_key = steps[idx - 1]['step_key']
            prev_prog = progress_map.get(prev_key)
            is_locked = not (prev_prog.is_done if prev_prog else False)

        merged.append({
            **step,
            'is_done': is_done,
            'is_locked': is_locked,
            'document_status': 'uploaded' if (prog and prog.document_path) else 'empty',
            'document_name': prog.document_name if prog else '',
        })
    return merged


def is_guidance_step(step_key: str) -> bool:
    return step_key in GUIDANCE_STEP_KEYS