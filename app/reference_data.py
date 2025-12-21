"""
Справочные данные по маркетплейсам.
Обновляются вручную при изменении тарифов.
"""

REFERENCE_VALUES = {
    # OZON
    "ozon": {
        "fbo": {  # FBO схемы
            "logistics_rub_per_sale": 120.0,  # Логистика "последняя миля"
            "storage_rub_per_sale": 15.0,     # Хранение за 30 дней
            "return_cost_rub": 200.0,         # Обработка возврата
            "other_fees_rub_per_sale": 25.0,  # Приёмка, обработка
            "opex_var_rub_per_sale": 10.0,    # Переменные расходы
        },
        "fbs": {  # FBS схемы
            "logistics_rub_per_sale": 80.0,   # Клиент платит часть
            "storage_rub_per_sale": 0.0,      # Нет хранения у Ozon
            "return_cost_rub": 150.0,
            "other_fees_rub_per_sale": 15.0,
            "opex_var_rub_per_sale": 10.0,
        }
    },
    
    # Wildberries
    "wb": {
        "fbo": {
            "logistics_rub_per_sale": 110.0,
            "storage_rub_per_sale": 18.0,
            "return_cost_rub": 180.0,
            "other_fees_rub_per_sale": 20.0,
            "opex_var_rub_per_sale": 8.0,
        },
        "fbs": {
            "logistics_rub_per_sale": 70.0,
            "storage_rub_per_sale": 0.0,
            "return_cost_rub": 140.0,
            "other_fees_rub_per_sale": 12.0,
            "opex_var_rub_per_sale": 8.0,
        }
    },
    
    # Яндекс Маркет
    "yandex": {
        "fbo": {
            "logistics_rub_per_sale": 130.0,
            "storage_rub_per_sale": 20.0,
            "return_cost_rub": 220.0,
            "other_fees_rub_per_sale": 30.0,
            "opex_var_rub_per_sale": 12.0,
        },
        "fbs": {
            "logistics_rub_per_sale": 90.0,
            "storage_rub_per_sale": 0.0,
            "return_cost_rub": 170.0,
            "other_fees_rub_per_sale": 18.0,
            "opex_var_rub_per_sale": 12.0,
        }
    },
    
    # СберМегаМаркет
    "sber": {
        "fbo": {
            "logistics_rub_per_sale": 140.0,
            "storage_rub_per_sale": 22.0,
            "return_cost_rub": 240.0,
            "other_fees_rub_per_sale": 35.0,
            "opex_var_rub_per_sale": 15.0,
        },
        "fbs": {
            "logistics_rub_per_sale": 100.0,
            "storage_rub_per_sale": 0.0,
            "return_cost_rub": 190.0,
            "other_fees_rub_per_sale": 22.0,
            "opex_var_rub_per_sale": 15.0,
        }
    },
    
    # Альтернативные маркетплейсы
    "ali": {
        "fbo": {
            "logistics_rub_per_sale": 180.0,  # Международная доставка
            "storage_rub_per_sale": 25.0,
            "return_cost_rub": 300.0,
            "other_fees_rub_per_sale": 40.0,
            "opex_var_rub_per_sale": 20.0,
        }
    }
}

def get_reference_value(marketplace: str, scheme: str, key: str) -> float:
    """
    Получить справочное значение для маркетплейса и схемы.
    Если нет значения, возвращает 0.0
    """
    mp_data = REFERENCE_VALUES.get(marketplace.lower())
    if not mp_data:
        return 0.0
    
    scheme_data = mp_data.get(scheme.lower())
    if not scheme_data:
        return 0.0
    
    return scheme_data.get(key, 0.0)
