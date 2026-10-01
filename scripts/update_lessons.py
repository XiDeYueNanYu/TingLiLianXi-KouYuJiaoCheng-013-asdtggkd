"""Đọc Google Sheet (CSV) và cập nhật lessons.json.
Cột JSON (mặc định A) chứa JSON của 1 bài học; cột cờ (mặc định B) = true thì bài được thêm/cập nhật.
Thứ tự dòng trong sheet: dòng dưới cùng là bài mới nhất."""
import csv, io, json, os, sys, urllib.parse, urllib.request

SHEET_ID = os.environ.get("SHEET_ID", "THAY_ID_GOOGLE_SHEET")
SHEET_TAB = os.environ.get("SHEET_TAB", "Sheet1")
JSON_COL = os.environ.get("JSON_COL", "A")   # đổi thành C, D... cho lớp khác
FLAG_COL = os.environ.get("FLAG_COL", "B")
OUT_FILE = os.environ.get("OUT_FILE", "lessons.json")

def col_index(letters):
    n = 0
    for ch in letters.upper():
        n = n * 26 + ord(ch) - 64
    return n - 1

def valid(lesson):
    if not isinstance(lesson, dict) or not lesson.get("title"):
        return False
    s = lesson.get("sentences")
    return isinstance(s, list) and s and all(isinstance(x, dict) and x.get("audio") and x.get("vi") and x.get("zh") for x in s)

url = (f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
       + urllib.parse.quote(SHEET_TAB))
try:
    raw = urllib.request.urlopen(url, timeout=60).read().decode("utf-8")
except Exception as e:
    sys.exit(f"Không đọc được Google Sheet: {e}")

try:
    with open(OUT_FILE, encoding="utf-8") as f:
        lessons = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    lessons = []
index = {l["id"]: k for k, l in enumerate(lessons)}

ji, fi = col_index(JSON_COL), col_index(FLAG_COL)
changed = 0
for n, row in enumerate(csv.reader(io.StringIO(raw)), start=1):
    if len(row) <= max(ji, fi) or row[fi].strip().lower() != "true":
        continue
    try:
        lesson = json.loads(row[ji])
    except json.JSONDecodeError as e:
        print(f"Dòng {n}: JSON lỗi, bỏ qua ({e})")
        continue
    if not valid(lesson):
        print(f"Dòng {n}: thiếu title/sentences(audio, vi, zh), bỏ qua")
        continue
    lesson.setdefault("id", lesson["title"])
    if lesson["id"] in index:          # trùng id: ghi đè nội dung, giữ vị trí
        if lessons[index[lesson["id"]]] != lesson:
            lessons[index[lesson["id"]]] = lesson; changed += 1
    else:                              # bài mới: thêm vào cuối (= mới nhất)
        index[lesson["id"]] = len(lessons); lessons.append(lesson); changed += 1

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(lessons, f, ensure_ascii=False, indent=1)
print(f"Xong. Tổng {len(lessons)} bài, {changed} bài thêm/cập nhật.")
