# src/data/morpho_metrics.py
import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

import pymorphy2


class MorphoMetrics:
    """
    Анализ частеречной структуры текста на русском языке.
    Поддерживает: существительные, глаголы, прилагательные, местоимения, наречия и др.
    Возвращает количества, доли и признаки для гипотез (например: "сказки → много глаголов совершенного вида").
    """

    def __init__(self, cache_size: int = 100_000):
        self.morph = pymorphy2.MorphAnalyzer()
        # Опционально: кэш для ускорения повторяющихся слов (актуально для сказок с повторами)
        self._cache = {}
        self._cache_size = cache_size

    def _normalize_word(self, word: str) -> str:
        return re.sub(r'[^а-яё]', '', word.lower())

    def _get_pos(self, word: str) -> str:
        """Возвращает часть речи (POS) для слова: NOUN, VERB, ADJF и т.д."""
        if not word:
            return "UNKNOWN"

        if word in self._cache:
            return self._cache[word]

        parsed = self.morph.parse(word)
        if not parsed:
            pos = "UNKNOWN"
        else:
            # Берём самый вероятный разбор
            pos = parsed[0].tag.POS or "UNKNOWN"

        # Ограничиваем кэш
        if len(self._cache) < self._cache_size:
            self._cache[word] = pos

        return pos

    def _extract_words(self, text: str) -> List[str]:
        """Извлекает только кириллические слова (без пунктуации, цифр)."""
        return re.findall(r'\b[а-яё]+\b', text.lower())

    def compute(self, text: str) -> Dict[str, int]:
        """
        Возвращает дескрипторы по частям речи.
        Все значения — целые числа или доли (float).
        """
        words = self._extract_words(text)
        if not words:
            return self._empty_result()

        pos_list = [self._get_pos(w) for w in words]
        pos_counter = Counter(pos_list)

        # Группировка по семантическим классам (как в лингвистике)
        noun_like = pos_counter["NOUN"] + pos_counter["NPRO"]  # NPRO = местоим-сущ (он, она, это)
        verb_like = pos_counter["VERB"] + pos_counter["INFN"] + pos_counter["GRND"]  # инфинитив, деепричастие
        adj_like = pos_counter["ADJF"] + pos_counter["PRTF"] + pos_counter["NUMR"]  # причастие, числительное как прил.
        adv_like = pos_counter["ADVB"]
        pronouns = pos_counter["NPRO"] + pos_counter["ADJPRO"] + pos_counter["PRTFPRO"]  # личные, притяж., отн.

        total = len(words)

        return {
            # Абсолютные количества (твои «существительные, глаголы и т.д.»)
            "nouns": pos_counter["NOUN"],
            "verbs": pos_counter["VERB"],
            "adjectives": pos_counter["ADJF"],
            "pronouns": pronouns,
            "adverbs": pos_counter["ADVB"],
            "prepositions": pos_counter["PREP"],
            "conjunctions": pos_counter["CONJ"],
            "particles": pos_counter["PRCL"],
            "interjections": pos_counter["INTJ"],

            # Производные — для гипотез и confidence
            "noun_ratio": round(pos_counter["NOUN"] / total, 3) if total else 0.0,
            "verb_ratio": round(pos_counter["VERB"] / total, 3) if total else 0.0,
            "adj_ratio": round(pos_counter["ADJF"] / total, 3) if total else 0.0,

            # Специфичные для сказок / сложности:
            "verb_perfective_ratio": self._compute_perfective_verb_ratio(words),
            "diminutive_noun_count": self._count_diminutives(words),
            "dialogue_markers": self._count_dialogue_markers(text),

            # Общие
            "total_words": total,
            "unique_lemmas": len({self.morph.parse(w)[0].normal_form
                                  for w in words if self.morph.parse(w)}),
        }

    def _compute_perfective_verb_ratio(self, words: List[str]) -> float:
        """Доля глаголов совершенного вида — важна для динамики (сказки: высокая)."""
        perfective_count = 0
        verb_count = 0
        for w in words:
            parses = self.morph.parse(w)
            if parses:
                tag = parses[0].tag
                if tag.POS in ("VERB", "INFN"):
                    verb_count += 1
                    if "perf" in tag.aspect:
                        perfective_count += 1
        return round(perfective_count / verb_count, 3) if verb_count else 0.0

    def _count_diminutives(self, words: List[str]) -> int:
        """Считает уменьшительно-ласкательные существительные (сказки: много!)."""
        suffixes = ("очк", "еньк", "оньк", "еньк", "ушк", "ышк", "ичк", "ичк")
        count = 0
        for w in words:
            norm = self.morph.parse(w)[0].normal_form if self.morph.parse(w) else w
            if any(norm.endswith(s) for s in suffixes):
                count += 1
        return count

    def _count_dialogue_markers(self, text: str) -> int:
        """Кавычки-«ёлочки», тире в начале строки — признак диалога (сказки: часто)."""
        count = 0
        count += len(re.findall(r'«[^»]*»', text))  # «речь»
        count += len(re.findall(r'^\s*—', text, re.MULTILINE))  # — сказал он
        return count

    @staticmethod
    def _empty_result() -> Dict[str, int]:
        keys = [
            "nouns", "verbs", "adjectives", "pronouns", "adverbs", "prepositions",
            "conjunctions", "particles", "interjections", "noun_ratio", "verb_ratio",
            "adj_ratio", "verb_perfective_ratio", "diminutive_noun_count",
            "dialogue_markers", "total_words", "unique_lemmas"
        ]
        return {k: 0 for k in keys}