# src/data/readability.py
import re
from typing import Dict, List

#from textComplexityMetrics import TextComplexityMetrics
#from descriptiveTextMetrics import DescriptiveTextMetrics

class TextComplexityMetrics:
    """
    Вычисляет базовые метрики сложности текста на русском (и частично — на других языках).
    Поддерживает гипотезы: короткие предложения + короткие слова → проще текст.
    """

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Разделяет текст на предложения (учитывает ..., !?, и т.д.)."""
        # Простой, но robust-подход для русского: точки, восклицания, вопросы — с последующими заглавными
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def _split_words(sentence: str) -> List[str]:
        """Извлекает слова (только буквы и дефисы внутри слов)."""
        return re.findall(r'\b[а-яА-ЯёЁa-zA-Z]+(?:-[а-яА-ЯёЁa-zA-Z]+)*\b', sentence)

    @staticmethod
    def _count_syllables_ru(word: str) -> int:
        """
        Подсчёт слогов в русском слове по гласным (е, ё, и, о, у, ы, э, ю, я, а).
        Простая, но эффективная эвристика — подходит для оценки сложности.
        """
        word = word.lower()
        vowels = "аеёиоуыэюя"
        return max(1, sum(1 for char in word if char in vowels))

    def compute(self, text: str) -> Dict[str, float]:
        """
        Возвращает словарь с метриками.
        Все значения округлены до 2 знаков для воспроизводимости и логгирования.
        """
        if not isinstance(text, str) or not text.strip():
            return {
                "avg_sentence_length": 0.0,
                "avg_word_syllables": 0.0,
                "avg_word_letters": 0.0,
                # доп. метрики для анализа
                "sentence_count": 0,
                "word_count": 0,
                "char_count": len(text),
                "confidence_hint": 0.0,
            }

        sentences = self._split_sentences(text)
        words = []
        for sent in sentences:
            words.extend(self._split_words(sent))

        # 1. Средняя длина предложения (в словах)
        avg_sent_len = len(words) / len(sentences) if sentences else 0

        # 2. Средняя длина слова в слогах
        syllables = [self._count_syllables_ru(w) for w in words]
        avg_syllables = sum(syllables) / len(syllables) if syllables else 0

        # 3. Средняя длина слова в буквах
        letters = [len(w) for w in words]
        avg_letters = sum(letters) / len(letters) if letters else 0

        # Confidence: если мало предложений/слов — низкая уверенность
        confidence = 1.0
        if len(sentences) < 2:
            confidence = 0.5
        if len(words) < 5:
            confidence = 0.3

        return {
            # Основные метрики
            "Средняя длина предложения (avg_sentence_length)": round(avg_sent_len, 2),
            "Средняя длина слова (в слогах) (avg_word_syllables)": round(avg_syllables, 2),
            "Средняя длина слова (в буквах) (аvg_word_letters)": round(avg_letters, 2),

            # Доп. для анализа и фильтрации
            "sentence_count": len(sentences),
            "word_count": len(words),
            "char_count": len(text),
            "confidence_hint": round(confidence, 2),
        }

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
            # 1–3: основные дескрипторы
            "word_forms_total": len(all_words),  # 1. словоформы (с повторами)
            "unique_words": len(unique_words),  # 2. уникальные слова
            "sentence_count": len(sentences),  # 3. предложений

            # 4–7: распределение по слогам (как в таблице)
            "monosyllabic_words": distribution.get(1, 0),  # 4. односложных
            "disyllabic_words": distribution.get(2, 0),  # 5. двусложных
            "trisyllabic_words": distribution.get(3, 0),  # 6. трёхсложных
            "polysyllabic_words": sum(v for k, v in distribution.items() if k >= 4),  # 7. ≥4 слогов

            # Дополнительно — для анализа и confidence
            "word_syllable_distribution": distribution,  # полное распределение: {1:6, 2:8, ...}
            "lexical_diversity": round(len(unique_words) / len(all_words), 3) if all_words else 0.0,
        }

class ReadabilityIndexCalculator:
    """
    Вычисляет индексы удобочитаемости (читабельности) для русского языка.
    Поддерживает:
      • Адаптированный индекс Флеша (Flesch Reading Ease для русского)
      • Индекс Смога (SMOG — для академических текстов)
      • Индекс «Просто о сложном» (российская методика)
      • Индекс школьной сложности (Минобрнауки РФ, 2020)
    """

    def __init__(self):
        self.complexity = TextComplexityMetrics()
        self.descriptive = DescriptiveTextMetrics()

    def _split_sentences(self, text: str) -> List[str]:
        return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

    def _extract_words(self, text: str) -> List[str]:
        return re.findall(r'\b[а-яё]+(?:-[а-яё]+)*\b', text.lower())

    def _count_syllables_ru(self, word: str) -> int:
        vowels = "аеёиоуыэюя"
        return max(1, sum(1 for ch in word if ch in vowels))

    def compute(self, text: str) -> Dict[str, float]:
        if not isinstance(text, str) or not text.strip():
            return self._empty_result()

        sentences = self._split_sentences(text)
        words = self._extract_words(text)

        n_sentences = len(sentences)
        n_words = len(words)
        if n_words == 0 or n_sentences == 0:
            return self._empty_result()

        # Слоги и длинные слова (≥4 слогов)
        syllables = [self._count_syllables_ru(w) for w in words]
        n_syllables = sum(syllables)
        polysyllables = sum(1 for s in syllables if s >= 3)  # ≥3 слогов — как в русских адаптациях

        # 1. Адаптированный индекс Флеша для русского (по методике Н. Ю. Сыромятниковой)
        # FRE = 206.835 − 1.3 * (слоги/слово) − 60.1 * (предл./слово)
        asl = n_words / n_sentences  # avg sentence length (в словах)
        asw = n_syllables / n_words  # avg syllables per word
        flesch = 206.835 - 1.3 * asw - 60.1 * (n_sentences / n_words)
        flesch = max(0.0, min(100.0, flesch))  # clamp to [0, 100]

        # 2. SMOG (Simple Measure of Gobbledygook) — адаптация для русского
        # SMOG = 1.043 * sqrt(30 * polysyllables / n_sentences) + 3.1291
        if n_sentences >= 10:
            smog = 1.043 * ((30.0 * polysyllables / n_sentences) ** 0.5) + 3.1291
        else:
            # для коротких текстов — линейная аппроксимация
            smog = 1.0 + 0.1 * polysyllables

        # 3. Индекс «Просто о сложном» (методика Госуслуг / РАНХиГС)
        # Баллы:
        #   +0.5 за каждое предложение > 15 слов
        #   +1.0 за каждое слово ≥4 слогов
        #   +0.2 за каждое слово ≥7 букв
        long_sentences = sum(1 for s in sentences if len(self._extract_words(s)) > 15)
        long_words = sum(1 for w in words if len(w) >= 7)
        polysyllables_4 = sum(1 for s in syllables if s >= 4)
        simple_score = 0.5 * long_sentences + 1.0 * polysyllables_4 + 0.2 * long_words
        simple_level = min(5.0, max(1.0, 1.0 + simple_score / 5.0))

        # 4. Школьный индекс (Минобрнауки РФ, 2020)
        # Уровень = 0.39 * (слов/предл.) + 11.8 * (слогов/слово) − 15.59
        school_level = 0.39 * asl + 11.8 * asw - 15.59
        school_level = max(1.0, min(12.0, school_level))  # 1–12 класс

        # Интерпретация (для логов и confidence)
        flesch_level = self._interpret_flesch(flesch)
        smog_grade = round(smog, 1)

        return {
            # Основные индексы
            "flesch_reading_ease": round(flesch, 1),  # 0–100: ↑ = легче
            "smog_grade": round(smog_grade, 1),  # ≈ класс школы
            "simple_level": round(simple_level, 1),  # 1–5: ↑ = сложнее
            "school_grade": round(school_level, 1),  # 1–12: класс

            # Промежуточные величины (для анализа и фич)
            "avg_sentence_words": round(asl, 2),
            "avg_word_syllables": round(asw, 2),
            "polysyllabic_words_ge3": polysyllables,  # ≥3 слогов
            "polysyllabic_words_ge4": polysyllables_4,  # ≥4 слогов
            "long_sentences_gt15": long_sentences,
            "long_words_ge7": long_words,

            # Интерпретации
            "flesch_level": flesch_level,  # "очень легко", "средне" и т.д.
            "is_child_friendly": flesch >= 70.0 and simple_level <= 2.5,
            "confidence_hint": 1.0 if n_words >= 20 else 0.6,
        }

    @staticmethod
    def _interpret_flesch(score: float) -> str:
        if score >= 90:
            return "очень легко (1–3 кл.)"
        elif score >= 80:
            return "легко (4–5 кл.)"
        elif score >= 70:
            return "довольно легко (6–7 кл.)"
        elif score >= 60:
            return "средне (8–9 кл.)"
        elif score >= 50:
            return "довольно сложно (10–11 кл.)"
        elif score >= 30:
            return "сложно (студенты)"
        else:
            return "очень сложно (академики)"

    @staticmethod
    def _empty_result() -> Dict[str, float]:
        return {
            "flesch_reading_ease": 0.0,
            "smog_grade": 0.0,
            "simple_level": 0.0,
            "school_grade": 0.0,
            "avg_sentence_words": 0.0,
            "avg_word_syllables": 0.0,
            "polysyllabic_words_ge3": 0,
            "polysyllabic_words_ge4": 0,
            "long_sentences_gt15": 0,
            "long_words_ge7": 0,
            "flesch_level": "пусто",
            "is_child_friendly": False,
            "confidence_hint": 0.0,
        }