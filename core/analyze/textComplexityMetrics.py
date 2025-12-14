# src/data/complexity_metrics.py
import re
from typing import Dict, List


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