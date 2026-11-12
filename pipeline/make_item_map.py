"""Bootstrap the TCB raw-name -> commodity mapping (run once, then review by hand).

TCB renames items over time ("রসুন (দেশী) নতুন/পুরাতন" -> "রসুন(দেশী)" -> ...), spells
the same word two ways (মশুর / মশূর) and has typos ("পিঁয়াজ (দেশী"). Each label
variant was verified to never co-occur with another variant on the same report,
so they are safely one series.

Outputs (the CSVs are the source of truth; edit them, not this script):
  data/reference/commodities.csv  - one row per canonical commodity
  data/reference/tcb_item_map.csv - every (item_raw, unit_raw) seen -> commodity_id

New labels that appear later are reported as UNMAPPED by build_dataset.py.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data" / "reference"

# id: (English name, category, unit, core basket?)
COMMODITIES = {
    "rice_fine": ("Rice, fine (Nazirshail/Miniket)", "Rice", "kg", 1),
    "rice_medium": ("Rice, medium (Pajam/BR-28)", "Rice", "kg", 1),
    "rice_coarse": ("Rice, coarse (Swarna/China IRRI)", "Rice", "kg", 1),
    "rice_aromatic": ("Rice, aromatic (polao), loose", "Rice", "kg", 0),
    "rice_aromatic_pkt": ("Rice, aromatic (polao), packet", "Rice", "kg", 0),
    "atta_loose": ("Atta, loose", "Flour", "kg", 1),
    "atta_pkt": ("Atta, packet", "Flour", "kg", 0),
    "maida_loose": ("Maida, loose", "Flour", "kg", 0),
    "maida_pkt": ("Maida, packet", "Flour", "kg", 0),
    "soybean_loose": ("Soybean oil, loose", "Edible oil", "litre", 1),
    "soybean_1l": ("Soybean oil, bottle 1 L", "Edible oil", "1 L bottle", 1),
    "soybean_2l": ("Soybean oil, bottle 2 L", "Edible oil", "2 L bottle", 0),
    "soybean_5l": ("Soybean oil, bottle 5 L", "Edible oil", "5 L bottle", 0),
    "palm_loose": ("Palm oil, loose", "Edible oil", "litre", 1),
    "palm_super_loose": ("Super palm oil, loose", "Edible oil", "litre", 0),
    "ricebran_1l": ("Rice bran oil, bottle 1 L", "Edible oil", "1 L bottle", 0),
    "ricebran_5l": ("Rice bran oil, bottle 5 L", "Edible oil", "5 L bottle", 0),
    "lentil_bold": ("Lentil (masur), bold grain", "Pulses", "kg", 1),
    "lentil_medium": ("Lentil (masur), medium grain", "Pulses", "kg", 0),
    "lentil_fine": ("Lentil (masur), fine grain", "Pulses", "kg", 0),
    "mung": ("Mung dal", "Pulses", "kg", 0),
    "anchor_dal": ("Anchor dal", "Pulses", "kg", 0),
    "chickpea": ("Chickpea (chola)", "Pulses", "kg", 1),
    "potato": ("Potato", "Vegetables", "kg", 1),
    "onion_local": ("Onion, local", "Vegetables", "kg", 1),
    "onion_imported": ("Onion, imported", "Vegetables", "kg", 0),
    "garlic_local": ("Garlic, local", "Vegetables", "kg", 1),
    "garlic_imported": ("Garlic, imported", "Vegetables", "kg", 0),
    "ginger_local": ("Ginger, local", "Vegetables", "kg", 0),
    "ginger_imported": ("Ginger, imported", "Vegetables", "kg", 1),
    "green_chili": ("Green chilli", "Vegetables", "kg", 0),
    "brinjal": ("Brinjal", "Vegetables", "kg", 0),
    "cucumber": ("Cucumber", "Vegetables", "kg", 0),
    "lemon": ("Lemon", "Vegetables", "hali (4 pcs)", 0),
    "chili_dry_local": ("Dry chilli, local", "Spices", "kg", 0),
    "chili_dry_imported": ("Dry chilli, imported", "Spices", "kg", 0),
    "turmeric_local": ("Turmeric, local", "Spices", "kg", 0),
    "turmeric_imported": ("Turmeric, imported", "Spices", "kg", 0),
    "cumin": ("Cumin", "Spices", "kg", 0),
    "cinnamon": ("Cinnamon", "Spices", "kg", 0),
    "clove": ("Clove", "Spices", "kg", 0),
    "cardamom": ("Cardamom (small)", "Spices", "kg", 0),
    "coriander": ("Coriander seed", "Spices", "kg", 0),
    "bay_leaf": ("Bay leaf", "Spices", "kg", 0),
    "rui": ("Rui fish", "Fish & meat", "kg", 1),
    "hilsa": ("Hilsa (ilish)", "Fish & meat", "kg", 1),
    "beef": ("Beef", "Fish & meat", "kg", 1),
    "mutton": ("Goat meat (khasi)", "Fish & meat", "kg", 0),
    "chicken_broiler": ("Chicken, broiler", "Fish & meat", "kg", 1),
    "chicken_local": ("Chicken, local (deshi)", "Fish & meat", "kg", 0),
    "eggs": ("Eggs, farm", "Eggs & dairy", "hali (4 pcs)", 1),
    "milk_dano": ("Milk powder, Dano", "Eggs & dairy", "kg", 0),
    "milk_diploma": ("Milk powder, Diploma", "Eggs & dairy", "kg", 0),
    "milk_fresh": ("Milk powder, Fresh", "Eggs & dairy", "kg", 0),
    "milk_marks": ("Milk powder, Marks", "Eggs & dairy", "kg", 0),
    "sugar": ("Sugar", "Other groceries", "kg", 1),
    "dates": ("Dates (khejur), regular", "Other groceries", "kg", 1),
    "salt": ("Salt, iodized, packet", "Other groceries", "kg", 0),
    "paper": ("Writing paper, white", "Non-food", "dista (24 sheets)", 0),
    "rod_60": ("MS rod, 60 grade", "Non-food", "metric ton", 0),
    "rod_40": ("MS rod, 40 grade", "Non-food", "metric ton", 0),
}

IMPORTED = "আমদানি"
# keyword -> id, checked in order after the special cases in rule()
SIMPLE = [
    ("জিরা", "cumin"), ("দারুচিনি", "cinnamon"), ("লবঙ্গ", "clove"), ("এলাচ", "cardamom"),
    ("ধনে", "coriander"), ("তেজপাতা", "bay_leaf"), ("রুই", "rui"), ("ইলিশ", "hilsa"),
    ("গরু", "beef"), ("খাসী", "mutton"), ("ব্রয়লার", "chicken_broiler"),
    ("মুরগী (দেশী)", "chicken_local"), ("ডিম", "eggs"), ("ডানো", "milk_dano"),
    ("ডিপ্লোমা", "milk_diploma"), ("ফ্রেশ", "milk_fresh"), ("মার্কস", "milk_marks"),
    ("চিনি", "sugar"), ("খেজুর", "dates"), ("লবণ", "salt"), ("কাগজ", "paper"),
    ("বেগুন", "brinjal"), ("শসা", "cucumber"), ("লেবু", "lemon"),
    ("মুগ", "mung"), ("এ্যাংকর", "anchor_dal"), ("ছোলা", "chickpea"), ("আলু", "potato"),
]
# (keyword, local id, imported id)
LOCAL_IMPORTED = [
    ("পিঁয়াজ", "onion_local", "onion_imported"),
    ("রসুন", "garlic_local", "garlic_imported"),
    ("আদা", "ginger_local", "ginger_imported"),
    ("শুকনা মরিচ", "chili_dry_local", "chili_dry_imported"),
    ("হলুদ", "turmeric_local", "turmeric_imported"),
]
def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


BOTTLE = {"১": "1l", "1": "1l", "2": "2l", "২": "2l", "৫": "5l", "5": "5l"}


def rule(item: str, unit: str) -> str | None:
    item, unit = nfc(item), nfc(unit)
    has =lambda *ws: all(w in item for w in ws)  # noqa: E731
    size = BOTTLE.get(unit[:1], "")
    if "সুগন্ধী" in item:
        return "rice_aromatic_pkt" if "প্যাঃ" in unit else "rice_aromatic"
    if has("চাল", "সরু"):
        return "rice_fine"
    if has("চাল", "মাঝারী"):
        return "rice_medium"
    if has("চাল", "মোটা"):
        return "rice_coarse"
    if "আটা" in item:
        return "atta_pkt" if "প্যাকেট" in item else "atta_loose"
    if "ময়দা" in item:
        return "maida_pkt" if "প্যাকেট" in item else "maida_loose"
    if "সয়াবিন" in item:
        return "soybean_loose" if "লুজ" in item else (f"soybean_{size}" if size else None)
    if "রাইস ব্রান" in item:
        return f"ricebran_{size}" if size else None
    if "পাম অলিন" in item:
        return f"palm_olein_{size}" if size else None
    if "পাম" in item:
        return "palm_super_loose" if "সুপার" in item else "palm_loose"
    if "মশ" in item and "ডাল" in item:  # মশুর / মশূর
        return "lentil_bold" if "বড়" in item else "lentil_fine" if "ছোট" in item else "lentil_medium"
    if "কাঁচামরিচ" in item:
        return "green_chili"
    for word, local, imported in LOCAL_IMPORTED:
        if word in item:
            return imported if IMPORTED in item else local
    for word, cid in SIMPLE:
        if word in item:
            return cid
    if "রড" in item:
        return "rod_60" if "৬০" in item else "rod_40"
    return None


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    from parse_tcb import load_observations
    obs = load_observations()
    pairs = obs[["item_raw", "unit_raw"]].drop_duplicates().fillna("")
    rows = []
    for item, unit in pairs.itertuples(index=False):
        cid, note = rule(item, unit), ""
        if unit[:1].isdigit() and "." in unit:  # e.g. unit cell "50.00-52.00"
            cid, note = None, "excluded: misaligned row (price in unit cell)"
        elif cid and cid.startswith("palm_olein"):
            cid, note = None, "excluded: listed on 4 days only (Apr 2025), 2L/5L prices swapped"
        rows.append((item, unit, cid or "", note or ("" if cid else "UNMAPPED")))
    m = pd.DataFrame(rows, columns=["item_raw", "unit_raw", "commodity_id", "note"])
    m = m.sort_values(["commodity_id", "item_raw"])
    m.to_csv(REF / "tcb_item_map.csv", index=False, encoding="utf-8")

    c = pd.DataFrame([(k, *v) for k, v in COMMODITIES.items()],
                     columns=["commodity_id", "name_en", "category", "unit", "core"])
    latest = (obs.merge(m, on=["item_raw"]).sort_values("report_date")
                 .groupby("commodity_id").item_raw.last())
    c["name_bn"] = c["commodity_id"].map(latest)
    c.to_csv(REF / "commodities.csv", index=False, encoding="utf-8")

    print(m.to_string(index=False))
    print("ids never matched:", sorted(set(COMMODITIES) - set(m.commodity_id)))
    print("excluded labels:", int(m["note"].str.startswith("excluded").sum()))
    print("ids not in COMMODITIES:", sorted(set(m.commodity_id) - set(COMMODITIES) - {""}))


if __name__ == "__main__":
    main()
