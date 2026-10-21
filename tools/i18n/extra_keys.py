"""Adds keys that were created after the big translation pass to every language file.
Run after the translators finished:  python extra_keys.py
"""
import json, os
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

ROOT = os.path.join(REPO, "src", "bdr", "i18n")

EXTRA = {
    "ui.quality": {
        "zh_CN": "DICE RUSH EXTENDED：动画质量", "zh_TW": "DICE RUSH EXTENDED：動畫品質", "ja": "DICE RUSH EXTENDED：アニメ品質",
        "ko": "DICE RUSH EXTENDED: 애니메이션 품질", "ru": "DICE RUSH EXTENDED: КАЧЕСТВО АНИМАЦИИ", "uk": "DICE RUSH EXTENDED: ЯКІСТЬ АНІМАЦІЇ",
        "bg": "DICE RUSH EXTENDED: КАЧЕСТВО НА АНИМАЦИЯТА", "pl": "DICE RUSH EXTENDED: JAKOŚĆ ANIMACJI", "es": "DICE RUSH EXTENDED: CALIDAD DE ANIMACIÓN",
        "es_419": "DICE RUSH EXTENDED: CALIDAD DE ANIMACIÓN", "pt_BR": "DICE RUSH EXTENDED: QUALIDADE DA ANIMAÇÃO",
        "pt_PT": "DICE RUSH EXTENDED: QUALIDADE DA ANIMAÇÃO", "fr": "DICE RUSH EXTENDED : QUALITÉ DES ANIMATIONS",
        "it": "DICE RUSH EXTENDED: QUALITÀ ANIMAZIONI", "ro": "DICE RUSH EXTENDED: CALITATEA ANIMAȚIEI", "nl": "DICE RUSH EXTENDED: ANIMATIEKWALITEIT",
        "da": "DICE RUSH EXTENDED: ANIMATIONSKVALITET", "sv": "DICE RUSH EXTENDED: ANIMATIONSKVALITET", "no": "DICE RUSH EXTENDED: ANIMASJONSKVALITET",
        "fi": "DICE RUSH EXTENDED: ANIMAATIOLAATU", "cs": "DICE RUSH EXTENDED: KVALITA ANIMACÍ", "hu": "DICE RUSH EXTENDED: ANIMÁCIÓ MINŐSÉGE",
        "el": "DICE RUSH EXTENDED: ΠΟΙΟΤΗΤΑ ΚΙΝΟΥΜΕΝΩΝ ΣΧΕΔΙΩΝ", "tr": "DICE RUSH EXTENDED: ANİMASYON KALİTESİ", "ar": "DICE RUSH EXTENDED: جودة الرسوم المتحركة",
        "th": "DICE RUSH EXTENDED: คุณภาพแอนิเมชัน", "vi": "DICE RUSH EXTENDED: CHẤT LƯỢNG HOẠT ẢNH", "id": "DICE RUSH EXTENDED: KUALITAS ANIMASI",
        "ms": "DICE RUSH EXTENDED: KUALITI ANIMASI",
    },
    "ui.quality_low": {
        "zh_CN": "低（流畅）", "zh_TW": "低（流暢）", "ja": "低（高速）", "ko": "낮음 (빠름)", "ru": "НИЗКОЕ (БЫСТРО)", "uk": "НИЗЬКА (ШВИДКО)",
        "bg": "НИСКО (БЪРЗО)", "pl": "NISKA (SZYBKO)", "es": "BAJA (RÁPIDA)", "es_419": "BAJA (RÁPIDA)", "pt_BR": "BAIXA (RÁPIDA)",
        "pt_PT": "BAIXA (RÁPIDA)", "fr": "BASSE (RAPIDE)", "it": "BASSA (VELOCE)", "ro": "SCĂZUTĂ (RAPID)", "nl": "LAAG (SNEL)",
        "da": "LAV (HURTIG)", "sv": "LÅG (SNABB)", "no": "LAV (RASK)", "fi": "MATALA (NOPEA)", "cs": "NÍZKÁ (RYCHLÁ)", "hu": "ALACSONY (GYORS)",
        "el": "ΧΑΜΗΛΗ (ΓΡΗΓΟΡΗ)", "tr": "DÜŞÜK (HIZLI)", "ar": "منخفضة (سريعة)", "th": "ต่ำ (เร็ว)", "vi": "THẤP (NHANH)", "id": "RENDAH (CEPAT)",
        "ms": "RENDAH (PANTAS)",
    },
    "ui.quality_medium": {
        "zh_CN": "中", "zh_TW": "中", "ja": "中", "ko": "보통", "ru": "СРЕДНЕЕ", "uk": "СЕРЕДНЯ", "bg": "СРЕДНО", "pl": "ŚREDNIA", "es": "MEDIA",
        "es_419": "MEDIA", "pt_BR": "MÉDIA", "pt_PT": "MÉDIA", "fr": "MOYENNE", "it": "MEDIA", "ro": "MEDIE", "nl": "GEMIDDELD", "da": "MIDDEL",
        "sv": "MEDEL", "no": "MIDDELS", "fi": "KESKITASO", "cs": "STŘEDNÍ", "hu": "KÖZEPES", "el": "ΜΕΣΑΙΑ", "tr": "ORTA", "ar": "متوسطة",
        "th": "ปานกลาง", "vi": "TRUNG BÌNH", "id": "SEDANG", "ms": "SEDERHANA",
    },
    "ui.quality_high": {
        "zh_CN": "高", "zh_TW": "高", "ja": "高", "ko": "높음", "ru": "ВЫСОКОЕ", "uk": "ВИСОКА", "bg": "ВИСОКО", "pl": "WYSOKA", "es": "ALTA",
        "es_419": "ALTA", "pt_BR": "ALTA", "pt_PT": "ALTA", "fr": "HAUTE", "it": "ALTA", "ro": "RIDICATĂ", "nl": "HOOG", "da": "HØJ", "sv": "HÖG",
        "no": "HØY", "fi": "KORKEA", "cs": "VYSOKÁ", "hu": "MAGAS", "el": "ΥΨΗΛΗ", "tr": "YÜKSEK", "ar": "عالية", "th": "สูง", "vi": "CAO",
        "id": "TINGGI", "ms": "TINGGI",
    },
}

EXTRA["tarot.owned"] = {
    "zh_CN": "已拥有 ×{n}", "zh_TW": "已擁有 ×{n}", "ja": "所持 ×{n}", "ko": "보유 ×{n}", "ru": "ИМЕЕТСЯ ×{n}",
    "uk": "НАЯВНА ×{n}", "bg": "ПРИТЕЖАНА ×{n}", "pl": "POSIADANA ×{n}", "es": "OBTENIDA ×{n}", "es_419": "OBTENIDA ×{n}",
    "pt_BR": "OBTIDA ×{n}", "pt_PT": "OBTIDA ×{n}", "fr": "POSSÉDÉE ×{n}", "it": "POSSEDUTA ×{n}", "ro": "DEȚINUTĂ ×{n}",
    "nl": "IN BEZIT ×{n}", "da": "EJET ×{n}", "sv": "ÄGS ×{n}", "no": "EID ×{n}", "fi": "OMISTETTU ×{n}",
    "cs": "VLASTNĚNÁ ×{n}", "hu": "MEGVAN ×{n}", "el": "ΣΤΗΝ ΚΑΤΟΧΗ ×{n}", "tr": "SAHİP ×{n}", "ar": "مملوكة ×{n}",
    "th": "มีแล้ว ×{n}", "vi": "ĐÃ CÓ ×{n}", "id": "DIMILIKI ×{n}", "ms": "DIMILIKI ×{n}",
}

EXTRA["ui.need_tier"] = {
    "zh_CN": "需要 {n} 个 {t} 级骰子（{have}/{n}）", "zh_TW": "需要 {n} 個 {t} 級骰子（{have}/{n}）",
    "ja": "ティア{t}のダイスが{n}個必要（{have}/{n}）", "ko": "{t}티어 주사위 {n}개 필요 ({have}/{n})",
    "ru": "Нужно {n} кубиков уровня {t} ({have}/{n})", "uk": "Потрібно {n} кубиків рівня {t} ({have}/{n})",
    "bg": "Нужни са {n} зара от ниво {t} ({have}/{n})", "pl": "Wymaga {n} kości poziomu {t} ({have}/{n})",
    "es": "Requiere {n} dados de nivel {t} ({have}/{n})", "es_419": "Requiere {n} dados de nivel {t} ({have}/{n})",
    "pt_BR": "Requer {n} dados do nível {t} ({have}/{n})", "pt_PT": "Requer {n} dados do nível {t} ({have}/{n})",
    "fr": "Nécessite {n} dés de niveau {t} ({have}/{n})", "it": "Servono {n} dadi di livello {t} ({have}/{n})",
    "ro": "Necesită {n} zaruri de nivel {t} ({have}/{n})", "nl": "Vereist {n} dobbelstenen van niveau {t} ({have}/{n})",
    "da": "Kræver {n} terninger på niveau {t} ({have}/{n})", "sv": "Kräver {n} tärningar på nivå {t} ({have}/{n})",
    "no": "Krever {n} terninger på nivå {t} ({have}/{n})", "fi": "Vaatii {n} tason {t} noppaa ({have}/{n})",
    "cs": "Vyžaduje {n} kostek úrovně {t} ({have}/{n})", "hu": "{n} darab {t}. szintű kocka kell ({have}/{n})",
    "el": "Απαιτεί {n} ζάρια επιπέδου {t} ({have}/{n})", "tr": "{t}. seviye {n} zar gerekir ({have}/{n})",
    "ar": "يتطلب {n} من نرد المستوى {t} ({have}/{n})", "th": "ต้องมีลูกเต๋าระดับ {t} จำนวน {n} ลูก ({have}/{n})",
    "vi": "Cần {n} xúc xắc cấp {t} ({have}/{n})", "id": "Butuh {n} dadu tingkat {t} ({have}/{n})",
    "ms": "Perlu {n} dadu peringkat {t} ({have}/{n})",
}


def main():
    for file_name in sorted(os.listdir(ROOT)):
        code = file_name[:-5]
        if not file_name.endswith(".json") or code in ("en", "de"):
            continue
        path = os.path.join(ROOT, file_name)
        data = json.load(open(path, encoding="utf-8"))
        changed = False
        for key, values in EXTRA.items():
            if key not in data and code in values:
                data[key] = values[code]
                changed = True
        if changed:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=1, sort_keys=True)
            print("updated", code)


if __name__ == "__main__":
    main()
