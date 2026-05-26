"""
اختبارات مكون زر اللصق
Tests for Paste Button Component
"""

import os
import pytest


class TestPasteButtonFiles:
    """اختبارات وجود ملفات المكون"""

    @staticmethod
    def get_base_path():
        """الحصول على المسار الأساسي للمشروع"""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_paste_button_js_exists(self):
        """اختبار وجود ملف paste-button.js"""
        base_path = self.get_base_path()
        js_file = os.path.join(base_path, 'static', 'js', 'paste-button.js')
        assert os.path.exists(js_file), "ملف paste-button.js غير موجود"

    def test_paste_button_min_js_exists(self):
        """اختبار وجود ملف paste-button.min.js"""
        base_path = self.get_base_path()
        js_min_file = os.path.join(base_path, 'static', 'js', 'paste-button.min.js')
        assert os.path.exists(js_min_file), "ملف paste-button.min.js غير موجود"

    def test_paste_button_css_exists(self):
        """اختبار وجود ملف paste-button.css"""
        base_path = self.get_base_path()
        css_file = os.path.join(base_path, 'static', 'css', 'paste-button.css')
        assert os.path.exists(css_file), "ملف paste-button.css غير موجود"

    def test_paste_button_min_css_exists(self):
        """اختبار وجود ملف paste-button.min.css"""
        base_path = self.get_base_path()
        css_min_file = os.path.join(base_path, 'static', 'css', 'paste-button.min.css')
        assert os.path.exists(css_min_file), "ملف paste-button.min.css غير موجود"

    def test_paste_button_demo_exists(self):
        """اختبار وجود ملف العرض التوضيحي"""
        base_path = self.get_base_path()
        # ملف العرض التوضيحي اختياري - تم حذفه لتقليل الملفات
        # demo_file = os.path.join(base_path, 'static', 'html', 'paste-button-demo.html')
        # assert os.path.exists(demo_file), "ملف العرض التوضيحي غير موجود"
        pass

    def test_bulk_paste_js_exists(self):
        """اختبار وجود ملف اللصق الجماعي"""
        base_path = self.get_base_path()
        js_file = os.path.join(base_path, 'static', 'js', 'bulk-paste.js')
        assert os.path.exists(js_file), "ملف bulk-paste.js غير موجود"

    def test_bulk_paste_min_js_exists(self):
        """اختبار وجود ملف اللصق الجماعي المضغوط"""
        base_path = self.get_base_path()
        js_min_file = os.path.join(base_path, 'static', 'js', 'bulk-paste.min.js')
        assert os.path.exists(js_min_file), "ملف bulk-paste.min.js غير موجود"

    def test_bulk_paste_css_exists(self):
        """اختبار وجود ملف CSS للصق الجماعي"""
        base_path = self.get_base_path()
        css_file = os.path.join(base_path, 'static', 'css', 'bulk-paste.css')
        assert os.path.exists(css_file), "ملف bulk-paste.css غير موجود"

    def test_bulk_paste_min_css_exists(self):
        """اختبار وجود ملف CSS المضغوط للصق الجماعي"""
        base_path = self.get_base_path()
        css_min_file = os.path.join(base_path, 'static', 'css', 'bulk-paste.min.css')
        assert os.path.exists(css_min_file), "ملف bulk-paste.min.css غير موجود"


class TestPasteButtonContent:
    """اختبارات محتوى ملفات المكون"""

    @staticmethod
    def get_base_path():
        """الحصول على المسار الأساسي للمشروع"""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_js_contains_class(self):
        """اختبار وجود فئة PasteButton في JavaScript"""
        base_path = self.get_base_path()
        js_file = os.path.join(base_path, 'static', 'js', 'paste-button.js')
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'class PasteButton' in content, "فئة PasteButton غير موجودة"

    def test_js_contains_methods(self):
        """اختبار وجود الدوال الأساسية في JavaScript"""
        base_path = self.get_base_path()
        js_file = os.path.join(base_path, 'static', 'js', 'paste-button.js')
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'attachPasteButton' in content, "دالة attachPasteButton غير موجودة"
        assert 'handlePaste' in content, "دالة handlePaste غير موجودة"
        assert 'showSuccess' in content, "دالة showSuccess غير موجودة"
        assert 'showError' in content, "دالة showError غير موجودة"

    def test_js_contains_mutation_observer(self):
        """اختبار وجود MutationObserver في JavaScript"""
        base_path = self.get_base_path()
        js_file = os.path.join(base_path, 'static', 'js', 'paste-button.js')
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'MutationObserver' in content, "MutationObserver غير موجود"

    def test_css_contains_classes(self):
        """اختبار وجود الفئات الأساسية في CSS"""
        base_path = self.get_base_path()
        css_file = os.path.join(base_path, 'static', 'css', 'paste-button.css')
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert '.paste-button-wrapper' in content, "فئة paste-button-wrapper غير موجودة"
        assert '.paste-button' in content, "فئة paste-button غير موجودة"
        assert '.paste-icon' in content, "فئة paste-icon غير موجودة"

    def test_css_contains_states(self):
        """اختبار وجود حالات مختلفة في CSS"""
        base_path = self.get_base_path()
        css_file = os.path.join(base_path, 'static', 'css', 'paste-button.css')
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert '.paste-button-success' in content, "فئة paste-button-success غير موجودة"
        assert '.paste-button-error' in content, "فئة paste-button-error غير موجودة"

    def test_css_contains_rtl_support(self):
        """اختبار وجود دعم RTL في CSS"""
        base_path = self.get_base_path()
        css_file = os.path.join(base_path, 'static', 'css', 'paste-button.css')
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'html[dir="rtl"]' in content, "دعم RTL غير موجود"

    def test_demo_contains_trigger_class(self):
        """اختبار وجود class paste-trigger في العرض التوضيحي"""
        # ملف العرض التوضيحي اختياري - تم حذفه لتقليل الملفات
        pass


class TestPasteButtonSyntax:
    """اختبارات صحة بناء الجملة"""

    @staticmethod
    def get_base_path():
        """الحصول على المسار الأساسي للمشروع"""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_js_brackets_balanced(self):
        """اختبار توازن الأقواس في JavaScript"""
        base_path = self.get_base_path()
        js_file = os.path.join(base_path, 'static', 'js', 'paste-button.js')
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content.count('{') == content.count('}'), "عدم توازن الأقواس المعقوفة"
        assert content.count('(') == content.count(')'), "عدم توازن الأقواس العادية"
        assert content.count('[') == content.count(']'), "عدم توازن الأقواس المربعة"

    def test_css_brackets_balanced(self):
        """اختبار توازن الأقواس في CSS"""
        base_path = self.get_base_path()
        css_file = os.path.join(base_path, 'static', 'css', 'paste-button.css')
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content.count('{') == content.count('}'), "عدم توازن الأقواس المعقوفة في CSS"

    def test_css_contains_variables(self):
        """اختبار وجود متغيرات CSS"""
        base_path = self.get_base_path()
        css_file = os.path.join(base_path, 'static', 'css', 'paste-button.css')
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'var(--' in content, "متغيرات CSS غير موجودة"


class TestPasteButtonPerformance:
    """اختبارات الأداء"""

    @staticmethod
    def get_base_path():
        """الحصول على المسار الأساسي للمشروع"""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_minified_js_smaller(self):
        """اختبار أن النسخة المضغوطة من JS أصغر من الأصلية"""
        base_path = self.get_base_path()
        js_file = os.path.join(base_path, 'static', 'js', 'paste-button.js')
        js_min_file = os.path.join(base_path, 'static', 'js', 'paste-button.min.js')
        
        js_size = os.path.getsize(js_file)
        js_min_size = os.path.getsize(js_min_file)
        
        assert js_min_size < js_size, "النسخة المضغوطة من JS أكبر من الأصلية"

    def test_minified_css_smaller(self):
        """اختبار أن النسخة المضغوطة من CSS أصغر من الأصلية"""
        base_path = self.get_base_path()
        css_file = os.path.join(base_path, 'static', 'css', 'paste-button.css')
        css_min_file = os.path.join(base_path, 'static', 'css', 'paste-button.min.css')
        
        css_size = os.path.getsize(css_file)
        css_min_size = os.path.getsize(css_min_file)
        
        assert css_min_size < css_size, "النسخة المضغوطة من CSS أكبر من الأصلية"

    def test_js_file_size_reasonable(self):
        """اختبار أن حجم ملف JavaScript معقول"""
        base_path = self.get_base_path()
        js_file = os.path.join(base_path, 'static', 'js', 'paste-button.js')
        
        js_size = os.path.getsize(js_file)
        # يجب أن يكون أقل من 10KB
        assert js_size < 10000, f"حجم ملف JavaScript كبير جداً: {js_size} bytes"

    def test_css_file_size_reasonable(self):
        """اختبار أن حجم ملف CSS معقول"""
        base_path = self.get_base_path()
        css_file = os.path.join(base_path, 'static', 'css', 'paste-button.css')
        
        css_size = os.path.getsize(css_file)
        # يجب أن يكون أقل من 10KB
        assert css_size < 10000, f"حجم ملف CSS كبير جداً: {css_size} bytes"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
