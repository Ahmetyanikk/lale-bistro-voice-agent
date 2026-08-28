from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MenuItem, RestaurantTable

TABLE_CAPACITIES = [2, 2, 4, 4, 4, 6, 8]

MENU_ITEMS = [
    ("Mercimek Corbasi", "Corba", 120.0, "Klasik kirmizi mercimek corbasi"),
    ("Ezogelin Corbasi", "Corba", 120.0, "Bulgur ve mercimekli baharatli corba"),
    ("Adana Kebap", "Ana Yemek", 380.0, "Acili izgara kiyma kebabi"),
    ("Karisik Izgara", "Ana Yemek", 520.0, "Kuzu pirzola, tavuk sis ve kofte"),
    ("Etli Guvec", "Ana Yemek", 340.0, "Firinda pisirilmis kuzu etli sebze guveci"),
    ("Mevsim Salata", "Salata", 160.0, "Taze mevsim yesillikleri"),
    ("Baklava", "Tatli", 220.0, "Fistikli geleneksel baklava"),
    ("Kunefe", "Tatli", 210.0, "Peynirli tel kadayif tatlisi"),
    ("Ayran", "Icecek", 60.0, "Ev yapimi yayik ayrani"),
    ("Turk Kahvesi", "Icecek", 90.0, "Geleneksel turk kahvesi"),
]


def seed_if_empty(db: Session) -> None:
    if db.execute(select(RestaurantTable.id)).first() is None:
        for i, capacity in enumerate(TABLE_CAPACITIES, start=1):
            db.add(RestaurantTable(label=f"T{i}", capacity=capacity))
    if db.execute(select(MenuItem.id)).first() is None:
        for name, category, price, description in MENU_ITEMS:
            db.add(MenuItem(name=name, category=category, price=price, description=description))
    db.commit()
