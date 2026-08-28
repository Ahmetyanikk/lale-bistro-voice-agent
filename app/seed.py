from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MenuItem, RestaurantTable

TABLE_CAPACITIES = [2, 2, 4, 4, 4, 6, 8]

MENU_ITEMS = [
    ("Mercimek Çorbası", "Çorba", 120.0, "Klasik kırmızı mercimek çorbası"),
    ("Ezogelin Çorbası", "Çorba", 120.0, "Bulgur ve mercimekli baharatlı çorba"),
    ("Adana Kebap", "Ana Yemek", 380.0, "Acılı ızgara kıyma kebabı"),
    # "Izgara" (capital dotless I) is the correct Turkish capitalization of
    # "ızgara" here — not a leftover ASCII workaround.
    ("Karışık Izgara", "Ana Yemek", 520.0, "Kuzu pirzola, tavuk şiş ve köfte"),
    ("Etli Güveç", "Ana Yemek", 340.0, "Fırında pişirilmiş kuzu etli sebze güveci"),
    ("Mevsim Salata", "Salata", 160.0, "Taze mevsim yeşillikleri"),
    ("Baklava", "Tatlı", 220.0, "Fıstıklı geleneksel baklava"),
    ("Künefe", "Tatlı", 210.0, "Peynirli tel kadayıf tatlısı"),
    ("Ayran", "İçecek", 60.0, "Ev yapımı yayık ayranı"),
    ("Türk Kahvesi", "İçecek", 90.0, "Geleneksel türk kahvesi"),
]

# vegetarian flag mirrors olovoice/knowledge_base.md and olovoice/menu_facts.json
VEGETARIAN_ITEMS = {
    "Mercimek Çorbası",
    "Ezogelin Çorbası",
    "Mevsim Salata",
    "Baklava",
    "Künefe",
    "Ayran",
    "Türk Kahvesi",
}


def seed_if_empty(db: Session) -> None:
    if db.execute(select(RestaurantTable.id)).first() is None:
        for i, capacity in enumerate(TABLE_CAPACITIES, start=1):
            db.add(RestaurantTable(label=f"T{i}", capacity=capacity))
    if db.execute(select(MenuItem.id)).first() is None:
        for name, category, price, description in MENU_ITEMS:
            db.add(MenuItem(name=name, category=category, price=price, description=description))
    db.commit()
