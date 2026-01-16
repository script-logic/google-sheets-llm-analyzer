"""
Анализ данных из Google Sheets.
Подсчет статистики, подготовка данных для LLM.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class AnalysisResult:
    """Результаты анализа данных."""

    total_requests: int
    total_rows: int
    category_counts: Dict[str, int]
    most_common_category: str
    most_common_count: int
    raw_data: List[List[Any]]

    @property
    def has_data(self) -> bool:
        """Есть ли данные для анализа."""
        return self.total_requests > 0

    @property
    def categories_sorted(self) -> List[Tuple[str, int]]:
        """Категории, отсортированные по количеству (по убыванию)."""
        return sorted(
            self.category_counts.items(), key=lambda x: x[1], reverse=True
        )


class DataAnalyzer:
    """Статистический анализатор данных из таблицы."""

    def __init__(self, category_column: int = 3):
        self.category_column = category_column

    def analyze(self, data: List[List[Any]]) -> AnalysisResult:
        """
        Анализирует данные таблицы.

        Args:
            data: Список строк таблицы (первая строка - заголовки)

        Returns:
            AnalysisResult с результатами анализа
        """
        if len(data) <= 1:
            return AnalysisResult(
                total_requests=0,
                total_rows=len(data),
                category_counts={},
                most_common_category="",
                most_common_count=0,
                raw_data=data,
            )

        categories = []
        skipped_rows = []

        for i, row in enumerate(data[1:], start=2):
            if len(row) >= self.category_column:
                category = row[self.category_column - 1]
                if isinstance(category, str):
                    category = category.strip()
                else:
                    category = str(category).strip() if category else ""

                if category:
                    categories.append(category)
                else:
                    skipped_rows.append(i)
            else:
                skipped_rows.append(i)

        print(f"⚠️  Пропущено {len(skipped_rows)} строк без категории")

        if not categories:
            return AnalysisResult(
                total_requests=0,
                total_rows=len(data),
                category_counts={},
                most_common_category="",
                most_common_count=0,
                raw_data=data,
            )

        category_counts = Counter(categories)

        if category_counts:
            most_common_category, most_common_count = (
                category_counts.most_common(1)[0]
            )
        else:
            most_common_category, most_common_count = "", 0

        return AnalysisResult(
            total_requests=len(categories),
            total_rows=len(data),
            category_counts=dict(category_counts),
            most_common_category=most_common_category,
            most_common_count=most_common_count,
            raw_data=data,
        )

    def get_requests_for_llm(
        self, data: List[List[Any]]
    ) -> List[Dict[str, Any]]:
        """
        Подготавливает данные для анализа LLM.

        Args:
            data: Сырые данные таблицы

        Returns:
            Список словарей с данными заявок
        """
        requests: List = []

        if len(data) <= 1:
            return requests

        # Структура таблицы:
        # A: Номер, B: Дата, C: Категория, D: Выбор
        for i, row in enumerate(data[1:], start=2):
            request_data = {
                "row_number": i,
                "id": row[0] if len(row) > 0 and row[0] else str(i),
                "date": row[1] if len(row) > 1 else "",
                "category": row[2] if len(row) > 2 else "",
                "choice": row[3] if len(row) > 3 else "",
            }

            # Очищаем строковые значения
            for key in request_data:
                str_clean = request_data[key]
                if isinstance(str_clean, str):
                    request_data[key] = str_clean.strip()
                elif request_data[key] is None:
                    request_data[key] = ""

            # Добавляем только если есть описание
            if request_data["choice"]:
                requests.append(request_data)

        if requests:
            print(
                f"✅ Найдено {len(requests)} заявок с описанием для"
                " анализа LLM"
            )
        else:
            print("ℹ️  Не найдено заявок с описанием для анализа LLM")

        return requests
