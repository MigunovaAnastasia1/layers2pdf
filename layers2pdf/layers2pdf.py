# layers2pdf.py
# Save to ~/.local/share/krita/pykrita/layers2pdf/

from krita import Extension, Krita, InfoObject
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PIL import Image
import os
import re
import shutil

class Layers2PDF(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        
    def setup(self):
        pass
        
    def createActions(self, window):
        action = window.createAction("layers_to_pdf", "Export Layers to PDF")
        action.triggered.connect(self.export_layers_to_pdf)
    
    def select_layers_by_sequence(self, nodes):
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
    
    def create_pdf_from_pngs(self, png_folder, pdf_path):
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
                break
        
        if len(valid_files) == 0:
            return 0
        
        # Создаём папку для PDF, если её нет
        pdf_dir = os.path.dirname(pdf_path)
        if pdf_dir and not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        # Конвертируем PNG в RGB и собираем в список
        images = []
        for path in valid_files:
            img = Image.open(path)
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                images.append(rgb_img)
            else:
                images.append(img.convert('RGB'))
        
        # Сохраняем PDF
        images[0].save(pdf_path, save_all=True, append_images=images[1:])
        return len(valid_files)
    
    def export_layers_to_pdf(self):
        # ============================================
        # 1. ПОЛУЧАЕМ АКТИВНЫЙ ДОКУМЕНТ
        # ============================================
        doc = Krita.instance().activeDocument()
        if not doc:
            QMessageBox.warning(
                None, 
                "Ошибка", 
                "❌ Нет открытого документа.\n\n"
                "Пожалуйста, откройте файл .kra и запустите плагин снова."
            )
            return
        
        file_name = doc.fileName()
        if not file_name:
            QMessageBox.warning(
                None, 
                "Ошибка", 
                "❌ Документ не сохранён на диск.\n\n"
                "Пожалуйста, сначала сохраните файл (Ctrl+S)."
            )
            return
        
        # ============================================
        # 2. ВЫБИРАЕМ КУДА СОХРАНИТЬ PDF
        # ============================================
        pdf_path = QFileDialog.getSaveFileName(
            None, 
            "Сохранить PDF-файл",
            os.path.dirname(file_name), 
            "PDF files (*.pdf)"
        )[0]
        
        if not pdf_path:
            return  # Пользователь отменил выбор
        
        # ============================================
        # 3. ПОДГОТОВКА К ЭКСПОРТУ
        # ============================================
        # Отключаем всплывающие диалоговые окна Krita
        doc.setBatchmode(True)
        
        # Получаем корневую ноду
        root = doc.rootNode()
        if not root:
            QMessageBox.warning(None, "Ошибка", "❌ Не удалось получить корневой узел документа")
            doc.setBatchmode(False)
            return
        
        # Получаем все слои
        all_nodes = root.childNodes()
        if not all_nodes:
            QMessageBox.warning(None, "Ошибка", "❌ В документе нет слоёв")
            doc.setBatchmode(False)
            return
        
        # Выбираем слои для экспорта
        export_nodes = self.select_layers_by_sequence(all_nodes)
        
        if len(export_nodes) == 0:
            QMessageBox.warning(
                None, 
                "Ошибка", 
                f"❌ Не найдено ни одного слоя для экспорта.\n\n"
                f"Слои, которые необходимо объединить в PDF, должны\n"
                f"называться \"1\", \"2\", \"3\" и т.д.\n\n"
                f"Проверьте наименование слоёв в файле:\n{os.path.basename(file_name)}"
            )
            doc.setBatchmode(False)
            return
        
        # ============================================
        # 4. СОЗДАЁМ ВРЕМЕННУЮ ПАПКУ ДЛЯ PNG
        # ============================================
        base_dir = os.path.dirname(file_name)
        export_dir = os.path.join(base_dir, "temp_png_export")
        
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
        os.makedirs(export_dir)
        
        # ============================================
        # 5. СОХРАНЯЕМ СОСТОЯНИЕ ВИДИМОСТИ СЛОЁВ
        # ============================================
        original_visibility = []
        def save_visibility(node, state_list):
            state_list.append((node, node.visible()))
            for child in node.childNodes():
                save_visibility(child, state_list)
        save_visibility(root, original_visibility)
        
        # Сохраняем текущий активный слой
        original_active_node = doc.activeNode()
        
        # ============================================
        # 6. ЭКСПОРТИРУЕМ СЛОИ В PNG
        # ============================================
        info = InfoObject()
        info.setProperty("alpha", True)
        info.setProperty("compression", 9)
        info.setProperty("forceSRGB", False)
        info.setProperty("indexed", False)
        info.setProperty("interlaced", False)
        info.setProperty("saveSRGBProfile", True)
        
        exported_count = 0
        
        for idx, node in enumerate(export_nodes, start=1):
            # Скрываем все слои
            for n in all_nodes:
                if (n.name() != "Background"):
                    n.setVisible(False)
                else:
                    n.setVisible(True)
            
            # Показываем только текущий
            node.setVisible(True)
            doc.refreshProjection()
            # Сохраняем PNG
            save_path = os.path.join(export_dir, f"page_{idx:04d}.png")
            if doc.exportImage(save_path, info):
                exported_count += 1
        
        # ============================================
        # 7. ВОССТАНАВЛИВАЕМ СОСТОЯНИЕ СЛОЁВ
        # ============================================
        def restore_visibility(state_list):
            for node, visible in state_list:
                node.setVisible(visible)
        restore_visibility(original_visibility)
        
        if original_active_node:
            doc.setActiveNode(original_active_node)
        
        doc.refreshProjection()
        doc.setBatchmode(False)
        
        # ============================================
        # 8. ПРОВЕРКА: ЕСТЬ ЛИ ЭКСПОРТИРОВАННЫЕ СТРАНИЦЫ
        # ============================================
        if exported_count == 0:
            QMessageBox.warning(
                None, 
                "Ошибка", 
                "❌ Не удалось экспортировать ни одной страницы.\n\n"
                "Проверьте, что слои с именами 1, 2, 3... содержат видимые изображения."
            )
            shutil.rmtree(export_dir)
            return
        
        # ============================================
        # 9. СОЗДАЁМ PDF ИЗ PNG
        # ============================================
        page_count = self.create_pdf_from_pngs(export_dir, pdf_path)
        
        # ============================================
        # 10. УДАЛЯЕМ ВРЕМЕННУЮ ПАПКУ
        # ============================================
        shutil.rmtree(export_dir)
        
        # ============================================
        # 11. ФИНАЛЬНОЕ ДИАЛОГОВОЕ ОКНО С РЕЗУЛЬТАТАМИ
        # ============================================
        if page_count > 0:
            QMessageBox.information(
                None, 
                "✅ Готово!", 
                f"PDF успешно создан!\n\n"
                f"📄 Страниц: {page_count}\n"
                f"🎯 Экспортировано слоёв: {exported_count}\n"
                f"📁 Файл: {pdf_path}\n\n"
                f"Временные файлы удалены."
            )
        else:
            QMessageBox.warning(
                None, 
                "Ошибка", 
                f"❌ Не удалось создать PDF.\n\n"
                f"Экспортировано PNG: {exported_count}\n"
                f"Ошибка при создании PDF из PNG."
            )

Krita.instance().addExtension(Layers2PDF(Krita.instance()))
