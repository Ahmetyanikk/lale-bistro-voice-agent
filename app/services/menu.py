from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MenuItem


def search_menu(db: Session, query: str | None, category: str | None) -> list[MenuItem]:
    stmt = select(MenuItem)
    if category:
        stmt = stmt.where(MenuItem.category.ilike(f"%{category}%"))
    if query:
        stmt = stmt.where(MenuItem.name.ilike(f"%{query}%"))
    stmt = stmt.order_by(MenuItem.category, MenuItem.name)
    return db.execute(stmt).scalars().all()
