# src/data/preprocessing.py
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Универсальная очистка: пробелы, спецсимволы, повторы."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'\s+', ' ', text)  # лишние пробелы → один
    text = re.sub(r'[^\w\s\-.,!?;:\"\']', ' ', text)  # оставить только буквы, цифры, пунктуацию
    text = text.strip()
    return text


def compute_text_features(text: str) -> Dict[str, float]:
    """Извлекает признаки для confidence-оценки и анализа."""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    return {
        "char_count": len(text),
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "avg_word_len": sum(len(w) for w in words) / len(words) if words else 0,
        "has_quotes": int('"' in text or "'" in text),
        "is_too_short": int(len(words) < 3),
        "is_too_long": int(len(words) > 512),  # порог для BERT
    }


def filter_by_quality(features: Dict[str, float], min_words: int = 5, max_words: int = 512) -> bool:
    """Фильтр: отсеиваем некачественные примеры (для train/val)."""
    return min_words <= features["word_count"] <= max_words and not features["is_too_short"]


def preprocess_example(example: Dict, text_field: str = "text") -> Dict:
    """
    Полная предобработка одного примера.
    Возвращает расширенный dict с очищенным текстом и признаками.
    """
    raw_text = example.get(text_field, "")
    cleaned = clean_text(raw_text)
    features = compute_text_features(cleaned)

    # Confidence-гипотеза: короткие/длинные тексты → низкая уверенность
    confidence_hint = 1.0
    if features["is_too_short"]:
        confidence_hint = 0.3
    elif features["is_too_long"]:
        confidence_hint = 0.6

    return {
        **example,
        "text_clean": cleaned,
        **{f"feat_{k}": v for k, v in features.items()},
        "confidence_hint": confidence_hint,
        "is_valid_for_training": filter_by_quality(features),
    }