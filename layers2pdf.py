# export_layers_cli.py
# Запуск: krita --export --script export_layers_cli.py -- --input file.kra

from krita import Krita, InfoObject
from PIL import Image
import sys
import os
import re
import shutil

#=========VARIABLES=============

# Название файла .kra
FILE_NAME = "lesson"
# Директория, в которой находится .kra
WORK_DIR = "/home/mimiguno/Reps/Layers2PDF/"
# Путь к исходному файлу .kra
INPUT_FILE = WORK_DIR + FILE_NAME + ".kra"

# Имя файла PDF
PDF_FILENAME = FILE_NAME + ".pdf"
# Путь для сохранения PDF
PDF_OUTPUT_PATH = WORK_DIR + "PDFs/" + PDF_FILENAME # Например: "/home/mimiguno/Desktop/result.pdf"

# Удалять ли временную папку export с PNG после создания PDF
DELETE_TEMP_FOLDER = True

# Настройки PNG экспорта
PNG_COMPRESSION = 9      # от 1 (быстро) до 9 (максимальное сжатие)
PNG_ALPHA = True         # сохранять прозрачность

def select_layers_by_sequence(nodes):
    """Выбирает узлы с непрерывной последовательностью чисел начиная с 1"""
    numbers = []
    for node in nodes:
        name = node.name()
        if name.isdigit():
            numbers.append((int(name), node))
    
    numbers.sort()
    result = []
    expected = 1
    
    for num, node in numbers:
        if num == expected:
            result.append(node)
            expected += 1
        elif num > expected:
            break
    
    return result


def create_pdf_from_pngs(png_folder, pdf_path):
    """
    Создаёт PDF из PNG файлов в папке.
    Возвращает количество страниц или 0 при ошибке.
    """
    # Собираем все PNG файлы с правильной нумерацией
    png_files = []
    for f in os.listdir(png_folder):
        match = re.match(r'page_(\d+)\.png', f)
        if match:
            page_num = int(match.group(1))
            png_files.append((page_num, os.path.join(png_folder, f)))
    
    if not png_files:
        print(f"❌ Не найдено png файлов для создания PDF.")
        print(f"   Нет файла page_0001.png")
        return 0
    
    # Сортируем по номеру страницы
    png_files.sort(key=lambda x: x[0])
    
    # Проверяем непрерывность последовательности
    expected = 1
    valid_files = []
    for num, path in png_files:
        if num == expected:
            valid_files.append(path)
            expected += 1
        else:
            print(f"⚠️ Пропущен файл page_{expected:04d}.png, останов на {num}")
            break
    
    print(f"\n📄 Создание PDF из {len(valid_files)} страниц...")
    
    # Конвертируем PNG в RGB и собираем в список
    images = []
    for idx, path in enumerate(valid_files, 1):
        print(f"   Страница {idx}: {os.path.basename(path)}")
        img = Image.open(path)
        
        # Конвертируем RGBA в RGB (PDF не поддерживает прозрачность)
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            images.append(rgb_img)
        else:
            images.append(img.convert('RGB'))
    
    pdf_dir = os.path.dirname(pdf_path)
    if pdf_dir and not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
        print(f"📁 Создана папка для PDF: {pdf_dir}")

    # Сохраняем PDF
    images[0].save(pdf_path, save_all=True, append_images=images[1:])
    
    print(f"   ✅ PDF создан: {pdf_path}")
    return len(valid_files)


def main():
    
    file_name = FILE_NAME + ".kra"
    input_file = INPUT_FILE
    
    if not os.path.exists(input_file):
        print(f"❌ Ошибка: файл не найден: {input_file}")
        sys.exit(1)
    
    print(f"📂 Открытие документа {file_name}...")
    
    # Открываем документ
    doc = Krita.instance().openDocument(input_file)
    if not doc:
        print(f"❌ Ошибка: не удалось открыть файл: {file_name}")
        sys.exit(1)
    
    print(f"✅ Документ открыт: {doc.fileName()}")
    
    # Отключаем всплывающие диалоговые окна Krita
    doc.setBatchmode(True)

    # Получаем корневую ноду
    root = doc.rootNode()

    if not root:
        print("❌ Ошибка: не удалось получить корневой узел")
        sys.exit(1)
    
    # Получаем все слои
    all_nodes = root.childNodes()
    
    if not all_nodes:
        print("❌ В документе нет слоёв, PDF не будет создано.")
        sys.exit(1)
    
    # Выбираем слои для экспорта
    export_nodes = select_layers_by_sequence(all_nodes)
    
    if len(export_nodes) == 0:
        print(f"❌ Ошибка: не найдено ни одного слоя для экспорта.")
        print(f"   Слои, которые необходимо объединить в PDF, должны")
        print(f"   называться \"1\", \"2\", \"3\" и т.д.")
        print(f"\n   Проверьте наименование слоев в {file_name}.")
        sys.exit(1)
    
    print(f"\n📊 Найдено слоёв для экспорта: {len(export_nodes)}")
    print(f"\n   Слои:")
    for i, node in enumerate(export_nodes, 1):
        print(f"   слой '{node.name()}'")
    
    # Создаём папку export
    base_dir = os.path.dirname(input_file)
    export_dir = os.path.join(base_dir, "export")
    
    if os.path.exists(export_dir):
    # Папка существует — очищаем её
        print(f"\n⚠️ Папка уже существует: {export_dir}")
        print(f"   Очистка старых файлов...")
        
        # Удаляем все PNG файлы в папке
        for file in os.listdir(export_dir):
            file_path = os.path.join(export_dir, file)
            os.remove(file_path)
            print(f"   Удалён файл: {file}")
        
        print(f"   ✅ Папка очищена")
    else:
        # Папки нет — создаём новую
        os.makedirs(export_dir)
        print(f"\n📁 Создана папка: {export_dir}")

    
    #====Backup видимости слоев============

    def save_visibility(node, state_list):
        state_list.append((node, node.visible()))
        for child in node.childNodes():
            save_visibility(child, state_list)

    original_visibility = []
    save_visibility(root, original_visibility)
    
    # Сохраняем текущий активный слой (тот, на котором пользователь работал)
    original_active_node = doc.activeNode()

    #========================================
    
    # Экспортируем слои
    exported_count = 0
    print(f"\n⏳ Экспорт страниц...")
    
    for idx, node in enumerate(export_nodes, start=1):
        print(f"   Страница {idx}: слой '{node.name()}'... ")
        
        # Скрываем все слои
        for n in all_nodes:
            if (n.name() != "Background"):
                n.setVisible(False)
            else:
                n.setVisible(True)
        
        # Показываем только текущий
        node.setVisible(True)
        doc.refreshProjection()
        
        # Настраиваем параметры для png изображения, в которое экпортируем слой
        save_path = os.path.join(export_dir, f"page_{idx:04d}.png")
        info = InfoObject()
        info.setProperty("alpha", PNG_ALPHA)
        info.setProperty("compression", PNG_COMPRESSION)
        info.setProperty("forceSRGB", False)
        info.setProperty("indexed", False)
        info.setProperty("interlaced", False)
        info.setProperty("saveSRGBProfile", True)
        
        if doc.exportImage(save_path, info):
            print("✅ Экпортирована")
            exported_count += 1
        else:
            print("❌")
    
    #=====Восстанавливаем первоначальное состояние слоев==========

    def restore_visibility(state_list):
        for node, visible in state_list:
            node.setVisible(visible)

    restore_visibility(original_visibility)
    
    # Восстанавливаем активный слой
    if original_active_node:
        doc.setActiveNode(original_active_node)
        print(f"\n📌 Восстановлен активный слой: '{original_active_node.name()}'")
    
    doc.refreshProjection()

    #============================================================
    
    print(f"\n{'='*50}")
    print(f"✅ Экспорт завершён!")
    print(f"   Страниц: {exported_count}")
    print(f"   Папка: {export_dir}")
    print(f"{'='*50}")

 #=================СОЗДАНИЕ PDF===================================================#

    if exported_count == 0:
        print("❌ Нет экспортированных страниц, PDF не создаётся")
        if DELETE_TEMP_FOLDER:
            shutil.rmtree(export_dir)
        sys.exit(1)
    
    # Создаём PDF из PNG
    print(f"\n{'='*50}")
    print(f"📄 СОЗДАНИЕ PDF")
    print(f"{'='*50}")
    
    page_count = create_pdf_from_pngs(export_dir, PDF_OUTPUT_PATH)
    
    if page_count > 0:
        print(f"\n{'='*50}")
        print(f"🎉 ГОТОВО!")
        print(f"   PDF: {PDF_OUTPUT_PATH}")
        print(f"   Страниц: {page_count}")
        print(f"{'='*50}")
    else:
        print(f"\n❌ Ошибка при создании PDF")
    
    # Удаляем временную папку с PNG
    if DELETE_TEMP_FOLDER:
        print(f"\n🗑️ Удаление временной папки: {export_dir}")
        shutil.rmtree(export_dir)
        print(f"   ✅ Папка удалена")
    
    print(f"\n✨ Готово!")



if __name__ == "__main__":
    main()
