#!/usr/bin/env python3
"""
Скрипт индексации PDF-книг для AI интерпретации.

ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:

1. Положите все PDF-книги по нумерологии в папку:
   backend/app/data/books/

2. Убедитесь, что в .env файле установлен OPENAI_API_KEY:
   OPENAI_API_KEY=your_api_key_here
   EMBEDDING_MODEL=text-embedding-3-small  (опционально)

3. Активируйте виртуальное окружение:
   cd backend
   source .venv/bin/activate  # или другой путь к вашему venv

4. Запустите скрипт:
   python -m scripts.index_books
   # или
   python scripts/index_books.py

5. Результат:
   - Скрипт обработает все PDF-файлы из папки books/
   - Для каждого PDF извлечёт текст и разобьёт на чанки
   - Для каждого чанка получит embedding через OpenAI
   - Сохранит результат в backend/app/data/ai_knowledge/chunks.json

6. После успешной индексации можно использовать AI интерпретацию в приложении.

ВНИМАНИЕ:
- Индексация может занять время (зависит от количества и размера книг)
- Используется API OpenAI, убедитесь, что у вас есть доступ и достаточный баланс
- При повторном запуске chunks.json будет перезаписан
"""
import sys
import os
from pathlib import Path
import json
import time
from typing import List, Dict

# Добавляем путь к app для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pdfplumber
except ImportError:
    print("ОШИБКА: pdfplumber не установлен. Установите: pip install pdfplumber")
    sys.exit(1)

try:
    from app.openai_client import get_embedding
except ImportError as e:
    print(f"ОШИБКА: Не удалось импортировать openai_client: {e}")
    print("Убедитесь, что OPENAI_API_KEY установлен в .env")
    sys.exit(1)


def extract_text_from_pdf(pdf_path: Path) -> List[Dict[str, any]]:
    """
    Извлечь текст из PDF постранично.
    
    Returns:
        Список словарей: [{"page": int, "text": str}, ...]
    """
    pages_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    # Нормализация текста
                    text = " ".join(text.split())  # Убираем лишние пробелы
                    pages_data.append({
                        "page": page_num,
                        "text": text
                    })
    except Exception as e:
        print(f"  ⚠️  Ошибка при чтении PDF {pdf_path.name}: {e}")
        return []
    
    return pages_data


def split_into_chunks(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """
    Разбить текст на чанки.
    
    Args:
        text: Исходный текст
        chunk_size: Размер чанка в символах
        overlap: Перекрытие между чанками
        
    Returns:
        Список строк-чанков
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Пытаемся разбить по границе предложения
        if end < len(text):
            # Ищем последнюю точку, восклицательный или вопросительный знак
            for i in range(end, max(start, end - 200), -1):
                if text[i] in '.!?':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if len(chunk) >= 100:  # Минимальный размер чанка
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def process_pdf(pdf_path: Path, chunk_id_start: int) -> tuple[List[Dict], int]:
    """
    Обработать один PDF файл.
    
    Returns:
        (список чанков, следующий доступный ID)
    """
    print(f"\n📖 Обработка: {pdf_path.name}")
    
    # Извлекаем текст постранично
    pages_data = extract_text_from_pdf(pdf_path)
    if not pages_data:
        print(f"  ⚠️  Не удалось извлечь текст из {pdf_path.name}")
        return [], chunk_id_start
    
    print(f"  📄 Извлечено страниц: {len(pages_data)}")
    
    # Разбиваем на чанки
    all_chunks = []
    for page_data in pages_data:
        page_num = page_data["page"]
        text = page_data["text"]
        chunks = split_into_chunks(text)
        
        for offset, chunk_text in enumerate(chunks, start=1):
            all_chunks.append({
                "page": page_num,
                "offset": offset,
                "text": chunk_text
            })
    
    print(f"  ✂️  Создано чанков: {len(all_chunks)}")
    
    # Получаем embeddings для каждого чанка
    chunks_with_embeddings = []
    for i, chunk in enumerate(all_chunks, 1):
        try:
            print(f"  🔄 Обработка чанка {i}/{len(all_chunks)}...", end="\r")
            embedding = get_embedding(chunk["text"])
            
            chunk_data = {
                "id": chunk_id_start + i - 1,
                "book": pdf_path.stem,  # Имя файла без расширения
                "page": chunk["page"],
                "offset": chunk["offset"],
                "text": chunk["text"],
                "embedding": embedding
            }
            chunks_with_embeddings.append(chunk_data)
            
            # Небольшая задержка, чтобы не превысить rate limits
            time.sleep(0.1)
        except Exception as e:
            print(f"\n  ⚠️  Ошибка при получении embedding для чанка {i}: {e}")
            continue
    
    print(f"  ✅ Обработано чанков: {len(chunks_with_embeddings)}")
    
    return chunks_with_embeddings, chunk_id_start + len(all_chunks)


def main():
    """Основная функция скрипта."""
    print("=" * 60)
    print("📚 ИНДЕКСАЦИЯ КНИГ ДЛЯ AI ИНТЕРПРЕТАЦИИ")
    print("=" * 60)
    
    # Определяем пути
    backend_dir = Path(__file__).parent.parent
    books_dir = backend_dir / "app" / "data" / "books"
    output_file = backend_dir / "app" / "data" / "ai_knowledge" / "chunks.json"
    
    # Проверяем папку с книгами
    if not books_dir.exists():
        print(f"❌ Папка {books_dir} не существует. Создаю...")
        books_dir.mkdir(parents=True, exist_ok=True)
    
    # Ищем все PDF файлы
    pdf_files = list(books_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n⚠️  В папке {books_dir} не найдено PDF-файлов.")
        print("   Положите PDF-книги в эту папку и запустите скрипт снова.")
        return
    
    print(f"\n📁 Найдено PDF-файлов: {len(pdf_files)}")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    
    # Создаём папку для результата
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Обрабатываем все PDF
    all_chunks = []
    chunk_id = 1
    start_time = time.time()
    
    for pdf_path in pdf_files:
        chunks, chunk_id = process_pdf(pdf_path, chunk_id)
        all_chunks.extend(chunks)
    
    elapsed_time = time.time() - start_time
    
    # Сохраняем результат
    print(f"\n💾 Сохранение результата в {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ ИНДЕКСАЦИЯ ЗАВЕРШЕНА!")
    print(f"   📊 Всего чанков: {len(all_chunks)}")
    print(f"   ⏱️  Время: {elapsed_time:.1f} секунд")
    print(f"   📁 Результат: {output_file}")
    print("\nТеперь можно использовать AI интерпретацию в приложении!")


if __name__ == "__main__":
    main()


