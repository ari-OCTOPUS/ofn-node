"""بستهٔ منطقِ ایجنت مارکتینگ زیمان (مستقل از مغزِ کنترل، پس تست‌پذیر)."""
from .product import (
    CommercialBlock,
    InventoryBlock,
    InventorySnapshot,
    PhotoProductMap,
    ProductCard,
    anti_misread_guard,
    capacity_fail_closed,
    hash_photo,
    index_photos,
    load_product_cards,
    next_product_id,
    save_product_card,
    valid_product_id,
)
from .telegram_adapter import ZimanTelegramAdapter

__all__ = [
    "CommercialBlock",
    "InventoryBlock",
    "InventorySnapshot",
    "PhotoProductMap",
    "ProductCard",
    "anti_misread_guard",
    "capacity_fail_closed",
    "hash_photo",
    "index_photos",
    "load_product_cards",
    "next_product_id",
    "save_product_card",
    "valid_product_id",
    "ZimanTelegramAdapter",
]
