import re
from typing import Dict, List, Tuple

class DescriptiveTextMetrics:
    """
    Вычисляет дескриптивные параметры текста:
    - слова vs. словоформы (с учётом повторов)
    - распределение слов по слогам
    - структура предложений

    Подходит для анализа сказок, учебных текстов, художественной речи.
    """

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Разделение на предложения (сохраняет надёжность)."""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def _extract_words(text: str) -> List[str]:
        """Извлекает слова в нижнем регистре, только кириллица + дефис внутри."""
        return re.findall(r'\b[а-яё]+(?:-[а-яё]+)*\b', text.lower())

    @staticmethod
    def _count_syllables_ru(word: str) -> int:
        """Слоги по гласным — как в классе выше, но вынесено для переиспользования."""
        vowels = "аеёиоуыэюя"
        return max(1, sum(1 for ch in word if ch in vowels))

    def compute(self, text: str) -> Dict[str, int]:
        """
        Возвращает словарь с дескриптивными параметрами.
        Все значения — целые числа (как в твоей таблице).
        """
        if not isinstance(text, str) or not text.strip():
            return {
                "word_forms_total": 0,
                "unique_words": 0,
                "sentence_count": 0,
                "monosyllabic_words": 0,
                "disyllabic_words": 0,
                "trisyllabic_words": 0,
                "polysyllabic_words": 0,  # ≥4 слогов
                "word_syllable_distribution": {},  # например: {1: 6, 2: 8, 3: 5, 4: 7}
            }

        sentences = self._split_sentences(text)
        all_words = self._extract_words(text)
        unique_words = set(all_words)

        # Подсчёт слогов для каждого слова
        syllable_counts = [self._count_syllables_ru(w) for w in all_words]

        # Группировка по количеству слогов
        distribution = {}
        for sc in syllable_counts:
            distribution[sc] = distribution.get(sc, 0) + 1

        return {
            "word_forms_total": len(all_words),  # 1. словоформы (с повторами)
            "Уникальные слова (unique_words)": len(unique_words),  # 2. уникальные слова
            "sentence_count": len(sentences),  # 3. предложений

            "monosyllabic_words": distribution.get(1, 0),  # 4. односложных
            "disyllabic_words": distribution.get(2, 0),  # 5. двусложных
            "trisyllabic_words": distribution.get(3, 0),  # 6. трёхсложных
            "polysyllabic_words": sum(v for k, v in distribution.items() if k >= 4),  # 7. ≥4 слогов

            "word_syllable_distribution": distribution,  # полное распределение: {1:6, 2:8, ...}
            "lexical_diversity": round(len(unique_words) / len(all_words), 3) if all_words else 0.0,
        }