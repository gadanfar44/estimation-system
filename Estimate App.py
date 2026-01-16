# -*- coding: utf-8 -*-
"""
تطبيق مهندس التقديرات - نسخة سطح المكتب
مخصص لمشاريع الأسفلت، الترابيات، الكهرباء، الأرصفة
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import os
import json

class EstimationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام تقدير تكاليف المشاريع الحكومية")
        self.root.geometry("1200x700")
        
        # تنسيق الألوان
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'light': '#ecf0f1',
            'dark': '#2c3e50'
        }
        
        # إنشاء مجلدات التطبيق
        self.create_app_folders()
        
        # إنشاء قاعدة البيانات
        self.init_database()
        
        # تحميل القوالب
        self.load_templates()
        
        # إنشاء الواجهة
        self.setup_ui()
        
        # تحميل البيانات الأولية
        self.load_initial_data()
    
    def create_app_folders(self):
        """إنشاء مجلدات التطبيق"""
        folders = ['data', 'exports', 'templates', 'backups']
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
    
    def init_database(self):
        """تهيئة قاعدة البيانات"""
        self.conn = sqlite3.connect('data/estimation.db')
        self.cursor = self.conn.cursor()
        
        # جدول الموردين
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                phone TEXT,
                specialization TEXT,
                rating INTEGER DEFAULT 3,
                last_update TEXT
            )
        ''')
        
        # جدول أسعار المواد
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT,
                unit TEXT,
                supplier_id INTEGER,
                price REAL,
                date TEXT,
                notes TEXT
            )
        ''')
        
        # جدول المشاريع
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                location TEXT,
                client TEXT,
                status TEXT,
                total_cost REAL DEFAULT 0,
                created_date TEXT,
                notes TEXT
            )
        ''')
        
        # جدول بنود المشروع
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                item_name TEXT,
                category TEXT,
                quantity REAL,
                unit TEXT,
                unit_price REAL,
                total_price REAL,
                notes TEXT
            )
        ''')
        
        self.conn.commit()
    
    def load_templates(self):
        """تحميل قوالب العمل"""
        self.templates = {
            "أسفلت": {
                "items": [
                    {"name": "خلطة أسفلت", "unit": "م³", "category": "مواد"},
                    {"name": "بيتومين", "unit": "طن", "category": "مواد"},
                    {"name": "عمال رصف", "unit": "يوم", "category": "عمالة"},
                    {"name": "فرادة أسفلت", "unit": "يوم", "category": "معدات"},
                    {"name": "مدحلة", "unit": "يوم", "category": "معدات"}
                ]
            },
            "أعمال ترابية": {
                "items": [
                    {"name": "تربة دفان", "unit": "م³", "category": "مواد"},
                    {"name": "رمل نظيف", "unit": "م³", "category": "مواد"},
                    {"name": "عمال حفر", "unit": "يوم", "category": "عمالة"},
                    {"name": "بوكلين", "unit": "يوم", "category": "معدات"},
                    {"name": "قلاب", "unit": "يوم", "category": "معدات"}
                ]
            },
            "كهرباء": {
                "items": [
                    {"name": "عمود إنارة", "unit": "وحدة", "category": "مواد"},
                    {"name": "كابل كهرباء", "unit": "متر", "category": "مواد"},
                    {"name": "لمبة LED", "unit": "وحدة", "category": "مواد"},
                    {"name": "فني كهرباء", "unit": "يوم", "category": "عمالة"}
                ]
            },
            "أرصفة": {
                "items": [
                    {"name": "بلاط إنترلوك", "unit": "م²", "category": "مواد"},
                    {"name": "بلدورة", "unit": "متر", "category": "مواد"},
                    {"name": "رمل فرش", "unit": "م³", "category": "مواد"},
                    {"name": "عمال بلاط", "unit": "يوم", "category": "عمالة"}
                ]
            }
        }
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # إنشاء شريط القوائم
        self.create_menu_bar()
        
        # إنشاء تبويبات رئيسية
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # تبويب الصفحة الرئيسية
        self.create_home_tab()
        
        # تبويب الموردين
        self.create_suppliers_tab()
        
        # تبويب المشاريع
        self.create_projects_tab()
        
        # تبويب التقدير
        self.create_estimation_tab()
        
        # تبويب التقارير
        self.create_reports_tab()
    
    def create_menu_bar(self):
        """إنشاء شريط القوائم"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # قائمة ملف
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ملف", menu=file_menu)
        file_menu.add_command(label="مشروع جديد", command=self.new_project)
        file_menu.add_command(label="فتح مشروع", command=self.open_project)
        file_menu.add_command(label="حفظ مشروع", command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label="تصدير لـ Excel", command=self.export_to_excel)
        file_menu.add_command(label="طباعة", command=self.print_report)
        file_menu.add_separator()
        file_menu.add_command(label="خروج", command=self.root.quit)
        
        # قائمة أدوات
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="أدوات", menu=tools_menu)
        tools_menu.add_command(label="نسخة احتياطية", command=self.create_backup)
        tools_menu.add_command(label="استعادة نسخة", command=self.restore_backup)
        tools_menu.add_command(label="إعدادات", command=self.open_settings)
        
        # قائمة مساعدة
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="مساعدة", menu=help_menu)
        help_menu.add_command(label="دليل المستخدم", command=self.show_help)
        help_menu.add_command(label="حول التطبيق", command=self.show_about)
    
    def create_home_tab(self):
        """إنشاء تبويب الصفحة الرئيسية"""
        home_frame = ttk.Frame(self.notebook)
        self.notebook.add(home_frame, text="🏠 الرئيسية")
        
        # العنوان
        title_label = tk.Label(home_frame, text="نظام تقدير تكاليف المشاريع الحكومية",
                              font=("Arial", 24, "bold"), fg=self.colors['primary'])
        title_label.pack(pady=20)
        
        # وصف التطبيق
        desc_text = """
        مميزات النظام:
        • إدارة قاعدة بيانات الموردين والأسعار
        • تقدير تكاليف مشاريع الأسفلت والأعمال الترابية
        • إدارة مشاريع الكهرباء والأرصفة
        • توليد تقارير تفصيلية للعروض
        • مقارنة أسعار الموردين
        """
        
        desc_label = tk.Label(home_frame, text=desc_text, font=("Arial", 12),
                             justify="right", fg=self.colors['dark'])
        desc_label.pack(pady=10)
        
        # أزرار سريعة
        buttons_frame = tk.Frame(home_frame)
        buttons_frame.pack(pady=30)
        
        quick_buttons = [
            ("🏗️ مشروع جديد", self.new_project, self.colors['secondary']),
            ("👥 إدارة الموردين", lambda: self.notebook.select(1), self.colors['success']),
            ("💰 تقدير التكاليف", lambda: self.notebook.select(3), self.colors['warning']),
            ("📊 التقارير", lambda: self.notebook.select(4), self.colors['primary'])
        ]
        
        for text, command, color in quick_buttons:
            btn = tk.Button(buttons_frame, text=text, command=command,
                          bg=color, fg="white", font=("Arial", 12, "bold"),
                          width=15, height=2, relief="raised", bd=2)
            btn.pack(side="left", padx=10)
        
        # إحصائيات
        stats_frame = tk.Frame(home_frame, bg=self.colors['light'], relief="ridge", bd=2)
        stats_frame.pack(pady=20, fill="x", padx=50)
        
        stats_data = [
            ("المشاريع النشطة", "12"),
            ("الموردين المسجلين", "24"),
            ("إجمالي التكاليف", "8.5M ريال"),
            ("آخر تحديث للأسعار", datetime.now().strftime("%Y-%m-%d"))
        ]
        
        for i, (label, value) in enumerate(stats_data):
            frame = tk.Frame(stats_frame, bg=self.colors['light'])
            frame.grid(row=0, column=i, padx=20, pady=10)
            
            lbl = tk.Label(frame, text=label, bg=self.colors['light'],
                          font=("Arial", 10), fg=self.colors['dark'])
            lbl.pack()
            
            val = tk.Label(frame, text=value, bg=self.colors['light'],
                          font=("Arial", 14, "bold"), fg=self.colors['primary'])
            val.pack()
    
    def create_suppliers_tab(self):
        """إنشاء تبويب الموردين"""
        suppliers_frame = ttk.Frame(self.notebook)
        self.notebook.add(suppliers_frame, text="👥 الموردون")
        
        # شريط أدوات الموردين
        toolbar = tk.Frame(suppliers_frame, bg=self.colors['light'])
        toolbar.pack(fill="x", pady=5)
        
        tk.Button(toolbar, text="➕ إضافة مورد", command=self.add_supplier,
                 bg=self.colors['success'], fg="white").pack(side="left", padx=5)
        tk.Button(toolbar, text="✏️ تعديل", command=self.edit_supplier,
                 bg=self.colors['warning'], fg="white").pack(side="left", padx=5)
        tk.Button(toolbar, text="🗑️ حذف", command=self.delete_supplier,
                 bg=self.colors['danger'], fg="white").pack(side="left", padx=5)
        tk.Button(toolbar, text="🔄 تحديث", command=self.refresh_suppliers,
                 bg=self.colors['secondary'], fg="white").pack(side="left", padx=5)
        
        # شجرة عرض الموردين
        columns = ("id", "الاسم", "التخصص", "الهاتف", "التقييم", "آخر تحديث")
        self.suppliers_tree = ttk.Treeview(suppliers_frame, columns=columns, show="headings")
        
        for col in columns:
            self.suppliers_tree.heading(col, text=col)
            self.suppliers_tree.column(col, width=100)
        
        self.suppliers_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # شريط تمرير
        scrollbar = ttk.Scrollbar(suppliers_frame, orient="vertical",
                                 command=self.suppliers_tree.yview)
        self.suppliers_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # تحميل بيانات الموردين
        self.refresh_suppliers()
    
    def create_projects_tab(self):
        """إنشاء تبويب المشاريع"""
        projects_frame = ttk.Frame(self.notebook)
        self.notebook.add(projects_frame, text="🏗️ المشاريع")
        
        # شريط أدوات المشاريع
        toolbar = tk.Frame(projects_frame, bg=self.colors['light'])
        toolbar.pack(fill="x", pady=5)
        
        tk.Button(toolbar, text="➕ مشروع جديد", command=self.new_project_dialog,
                 bg=self.colors['success'], fg="white").pack(side="left", padx=5)
        tk.Button(toolbar, text="📋 تفاصيل", command=self.show_project_details,
                 bg=self.colors['secondary'], fg="white").pack(side="left", padx=5)
        tk.Button(toolbar, text="🗑️ حذف", command=self.delete_project,
                 bg=self.colors['danger'], fg="white").pack(side="left", padx=5)
        
        # شجرة عرض المشاريع
        columns = ("id", "اسم المشروع", "النوع", "الموقع", "الحالة", "التكلفة")
        self.projects_tree = ttk.Treeview(projects_frame, columns=columns, show="headings")
        
        for col in columns:
            self.projects_tree.heading(col, text=col)
            self.projects_tree.column(col, width=120)
        
        self.projects_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # تحميل بيانات المشاريع
        self.refresh_projects()
    
    def create_estimation_tab(self):
        """إنشاء تبويب تقدير التكاليف"""
        estimation_frame = ttk.Frame(self.notebook)
        self.notebook.add(estimation_frame, text="💰 التقدير")
        
        # إطار الإدخال
        input_frame = tk.LabelFrame(estimation_frame, text="إدخال بيانات البند",
                                   font=("Arial", 12, "bold"))
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # اسم البند
        tk.Label(input_frame, text="اسم البند:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.item_name_entry = tk.Entry(input_frame, width=30)
        self.item_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # الفئة
        tk.Label(input_frame, text="الفئة:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.category_var = tk.StringVar()
        category_combo = ttk.Combobox(input_frame, textvariable=self.category_var,
                                     values=["مواد", "عمالة", "معدات", "نقل"])
        category_combo.grid(row=0, column=3, padx=5, pady=5)
        category_combo.set("مواد")
        
        # الكمية
        tk.Label(input_frame, text="الكمية:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.quantity_entry = tk.Entry(input_frame, width=10)
        self.quantity_entry.grid(row=1, column=1, padx=5, pady=5)
        self.quantity_entry.insert(0, "1")
        
        # الوحدة
        tk.Label(input_frame, text="الوحدة:").grid(row=1, column=2, sticky="e", padx=5, pady=5)
        self.unit_entry = tk.Entry(input_frame, width=10)
        self.unit_entry.grid(row=1, column=3, padx=5, pady=5)
        self.unit_entry.insert(0, "م³")
        
        # سعر الوحدة
        tk.Label(input_frame, text="سعر الوحدة:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.unit_price_entry = tk.Entry(input_frame, width=15)
        self.unit_price_entry.grid(row=2, column=1, padx=5, pady=5)
        self.unit_price_entry.insert(0, "0")
        
        # زر إضافة
        tk.Button(input_frame, text="➕ إضافة البند", command=self.add_estimation_item,
                 bg=self.colors['success'], fg="white").grid(row=2, column=3, padx=5, pady=5)
        
        # زر استخدام قالب
        tk.Button(input_frame, text="🧱 استخدام قالب", command=self.use_template,
                 bg=self.colors['secondary'], fg="white").grid(row=2, column=2, padx=5, pady=5)
        
        # شجرة البنود المضافة
        columns = ("الاسم", "الفئة", "الكمية", "الوحدة", "سعر الوحدة", "الإجمالي")
        self.estimation_tree = ttk.Treeview(estimation_frame, columns=columns, show="headings")
        
        for col in columns:
            self.estimation_tree.heading(col, text=col)
            self.estimation_tree.column(col, width=100)
        
        self.estimation_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        # الإجماليات
        total_frame = tk.Frame(estimation_frame)
        total_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(total_frame, text="إجمالي المواد:", font=("Arial", 11, "bold")).pack(side="left", padx=10)
        self.material_total_label = tk.Label(total_frame, text="0 ريال", font=("Arial", 11, "bold"),
                                            fg=self.colors['success'])
        self.material_total_label.pack(side="left", padx=10)
        
        tk.Label(total_frame, text="إجمالي العمالة:", font=("Arial", 11, "bold")).pack(side="left", padx=10)
        self.labor_total_label = tk.Label(total_frame, text="0 ريال", font=("Arial", 11, "bold"),
                                         fg=self.colors['warning'])
        self.labor_total_label.pack(side="left", padx=10)
        
        tk.Label(total_frame, text="الإجمالي الكلي:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.grand_total_label = tk.Label(total_frame, text="0 ريال", font=("Arial", 12, "bold"),
                                         fg=self.colors['primary'])
        self.grand_total_label.pack(side="left", padx=10)
        
        # أزرار الحفظ
        btn_frame = tk.Frame(estimation_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="💾 حفظ التقدير", command=self.save_estimation,
                 bg=self.colors['primary'], fg="white", width=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️ مسح الكل", command=self.clear_estimation,
                 bg=self.colors['danger'], fg="white", width=15).pack(side="left", padx=5)
    
    def create_reports_tab(self):
        """إنشاء تبويب التقارير"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="📊 التقارير")
        
        # خيارات التقرير
        options_frame = tk.LabelFrame(reports_frame, text="خيارات التقرير",
                                     font=("Arial", 12, "bold"))
        options_frame.pack(fill="x", padx=10, pady=5)
        
        # نوع التقرير
        tk.Label(options_frame, text="نوع التقرير:").grid(row=0, column=0, padx=5, pady=5)
        self.report_type = tk.StringVar()
        report_combo = ttk.Combobox(options_frame, textvariable=self.report_type,
                                   values=["تقرير تكاليف", "مقارنة أسعار", "ملخص المشاريع"])
        report_combo.grid(row=0, column=1, padx=5, pady=5)
        report_combo.set("تقرير تكاليف")
        
        # نطاق التاريخ
        tk.Label(options_frame, text="من تاريخ:").grid(row=0, column=2, padx=5, pady=5)
        self.from_date = tk.Entry(options_frame, width=12)
        self.from_date.grid(row=0, column=3, padx=5, pady=5)
        self.from_date.insert(0, datetime.now().strftime("%Y-%m-01"))
        
        tk.Label(options_frame, text="إلى تاريخ:").grid(row=0, column=4, padx=5, pady=5)
        self.to_date = tk.Entry(options_frame, width=12)
        self.to_date.grid(row=0, column=5, padx=5, pady=5)
        self.to_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # زر توليد التقرير
        tk.Button(options_frame, text="🔄 توليد التقرير", command=self.generate_report,
                 bg=self.colors['secondary'], fg="white").grid(row=0, column=6, padx=10, pady=5)
        
        # منطقة عرض التقرير
        self.report_text = tk.Text(reports_frame, height=20, width=100,
                                  font=("Courier New", 10))
        self.report_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # أزرار التصدير
        export_frame = tk.Frame(reports_frame)
        export_frame.pack(pady=5)
        
        tk.Button(export_frame, text="📥 حفظ كملف نصي", command=self.save_report_txt,
                 bg=self.colors['success'], fg="white").pack(side="left", padx=5)
        tk.Button(export_frame, text="🖨️ طباعة", command=self.print_report,
                 bg=self.colors['primary'], fg="white").pack(side="left", padx=5)
    
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        try:
            # تحقق من وجود بيانات الموردين
            self.cursor.execute("SELECT COUNT(*) FROM suppliers")
            count = self.cursor.fetchone()[0]
            
            if count == 0:
                self.add_sample_data()
                
        except Exception as e:
            print(f"Error loading initial data: {e}")
    
    def add_sample_data(self):
        """إضافة بيانات تجريبية"""
        # إضافة موردين
        suppliers = [
            ("شركة الأسفلت الوطنية", "محمد أحمد", "0555123456", "أسفلت", 4),
            ("مؤسسة التربة والردم", "سعود المري", "0500987654", "تربة", 5),
            ("شركة الكهرباء المتقدمة", "خالد الغامدي", "0566778899", "كهرباء", 4),
            ("مصنع الإنترلوك الحديث", "علي السعد", "0544332211", "أرصفة", 3)
        ]
        
        for supplier in suppliers:
            self.cursor.execute('''
                INSERT INTO suppliers (name, contact, phone, specialization, rating, last_update)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (*supplier, datetime.now().strftime("%Y-%m-%d")))
        
        # إضافة أسعار مواد
        prices = [
            ("خلطة أسفلت", "أسفلت", "م³", 1, 150.0),
            ("بيتومين", "أسفلت", "طن", 1, 2000.0),
            ("تربة دفان", "تربة", "م³", 2, 40.0),
            ("رمل نظيف", "تربة", "م³", 2, 30.0),
            ("عمود إنارة 10م", "كهرباء", "وحدة", 3, 850.0),
            ("كابل كهرباء 16مم", "كهرباء", "متر", 3, 12.0),
            ("بلاط إنترلوك", "أرصفة", "م²", 4, 45.0),
            ("بلدورة خرسانية", "أرصفة", "متر", 4, 18.0)
        ]
        
        for price in prices:
            self.cursor.execute('''
                INSERT INTO prices (item_name, category, unit, supplier_id, price, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (*price, datetime.now().strftime("%Y-%m-%d")))
        
        # إضافة مشاريع تجريبية
        projects = [
            ("رصف طريق الملك فهد", "أسفلت", "الرياض", "أمانة الرياض", "جاري التنفيذ", 2850000),
            ("توريد تربة دفان", "أعمال ترابية", "جدة", "جامعة الملك عبدالعزيز", "تقديم عرض", 850000),
            ("إنارة حديقة عامة", "كهرباء", "الدمام", "أمانة الشرقية", "مكتمل", 420000)
        ]
        
        for project in projects:
            self.cursor.execute('''
                INSERT INTO projects (name, type, location, client, status, total_cost, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (*project, datetime.now().strftime("%Y-%m-%d")))
        
        self.conn.commit()
        messagebox.showinfo("تهيئة البيانات", "تم إضافة بيانات تجريبية بنجاح!")
    
    # ===== دوال الموردين =====
    def refresh_suppliers(self):
        """تحديث قائمة الموردين"""
        # مسح البيانات القديمة
        for item in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(item)
        
        # جلب البيانات من قاعدة البيانات
        self.cursor.execute('''
            SELECT id, name, specialization, phone, rating, last_update
            FROM suppliers ORDER BY name
        ''')
        
        suppliers = self.cursor.fetchall()
        
        # إضافة البيانات للشجرة
        for supplier in suppliers:
            self.suppliers_tree.insert("", "end", values=supplier)
    
    def add_supplier(self):
        """إضافة مورد جديد"""
        dialog = tk.Toplevel(self.root)
        dialog.title("إضافة مورد جديد")
        dialog.geometry("400x300")
        
        # حقول الإدخال
        tk.Label(dialog, text="اسم المورد:").pack(pady=5)
        name_entry = tk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="اسم المسؤول:").pack(pady=5)
        contact_entry = tk.Entry(dialog, width=40)
        contact_entry.pack(pady=5)
        
        tk.Label(dialog, text="رقم الهاتف:").pack(pady=5)
        phone_entry = tk.Entry(dialog, width=40)
        phone_entry.pack(pady=5)
        
        tk.Label(dialog, text="التخصص:").pack(pady=5)
        spec_entry = tk.Entry(dialog, width=40)
        spec_entry.pack(pady=5)
        
        def save_supplier():
            name = name_entry.get()
            contact = contact_entry.get()
            phone = phone_entry.get()
            specialization = spec_entry.get()
            
            if name:
                try:
                    self.cursor.execute('''
                        INSERT INTO suppliers (name, contact, phone, specialization, rating, last_update)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (name, contact, phone, specialization, 3, datetime.now().strftime("%Y-%m-%d")))
                    
                    self.conn.commit()
                    self.refresh_suppliers()
                    dialog.destroy()
                    messagebox.showinfo("نجاح", "تم إضافة المورد بنجاح!")
                except Exception as e:
                    messagebox.showerror("خطأ", f"حدث خطأ: {e}")
            else:
                messagebox.showwarning("تحذير", "يرجى إدخال اسم المورد")
        
        tk.Button(dialog, text="💾 حفظ", command=save_supplier,
                 bg=self.colors['success'], fg="white").pack(pady=20)
    
    def edit_supplier(self):
        """تعديل بيانات المورد"""
        selected = self.suppliers_tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "يرجى اختيار مورد للتعديل")
            return
        
        item = self.suppliers_tree.item(selected[0])
        supplier_id = item['values'][0]
        
        # فتح نافذة التعديل
        dialog = tk.Toplevel(self.root)
        dialog.title("تعديل بيانات المورد")
        dialog.geometry("400x300")
        
        # جلب بيانات المورد
        self.cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
        supplier = self.cursor.fetchone()
        
        # حقول الإدخال
        tk.Label(dialog, text="اسم المورد:").pack(pady=5)
        name_entry = tk.Entry(dialog, width=40)
        name_entry.insert(0, supplier[1])
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="رقم الهاتف:").pack(pady=5)
        phone_entry = tk.Entry(dialog, width=40)
        phone_entry.insert(0, supplier[3])
        phone_entry.pack(pady=5)
        
        tk.Label(dialog, text="التخصص:").pack(pady=5)
        spec_entry = tk.Entry(dialog, width=40)
        spec_entry.insert(0, supplier[4])
        spec_entry.pack(pady=5)
        
        def update_supplier():
            try:
                self.cursor.execute('''
                    UPDATE suppliers SET name = ?, phone = ?, specialization = ?, last_update = ?
                    WHERE id = ?
                ''', (name_entry.get(), phone_entry.get(), spec_entry.get(),
                     datetime.now().strftime("%Y-%m-%d"), supplier_id))
                
                self.conn.commit()
                self.refresh_suppliers()
                dialog.destroy()
                messagebox.showinfo("نجاح", "تم تحديث بيانات المورد!")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}")
        
        tk.Button(dialog, text="💾 حفظ التعديلات", command=update_supplier,
                 bg=self.colors['success'], fg="white").pack(pady=20)
    
    def delete_supplier(self):
        """حذف مورد"""
        selected = self.suppliers_tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "يرجى اختيار مورد للحذف")
            return
        
        item = self.suppliers_tree.item(selected[0])
        supplier_name = item['values'][1]
        
        if messagebox.askyesno("تأكيد", f"هل تريد حذف المورد '{supplier_name}'؟"):
            try:
                supplier_id = item['values'][0]
                self.cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
                self.conn.commit()
                self.refresh_suppliers()
                messagebox.showinfo("نجاح", "تم حذف المورد بنجاح!")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}")
    
    # ===== دوال المشاريع =====
    def refresh_projects(self):
        """تحديث قائمة المشاريع"""
        # مسح البيانات القديمة
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)
        
        # جلب البيانات من قاعدة البيانات
        self.cursor.execute('''
            SELECT id, name, type, location, status, total_cost
            FROM projects ORDER BY created_date DESC
        ''')
        
        projects = self.cursor.fetchall()
        
        # إضافة البيانات للشجرة
        for project in projects:
            # تنسيق التكلفة
            formatted_project = list(project)
            formatted_project[5] = f"{project[5]:,.0f} ريال" if project[5] else "0 ريال"
            self.projects_tree.insert("", "end", values=formatted_project)
    
    def new_project_dialog(self):
        """نافذة إنشاء مشروع جديد"""
        dialog = tk.Toplevel(self.root)
        dialog.title("مشروع جديد")
        dialog.geometry("500x400")
        
        # حقول الإدخال
        fields = [
            ("اسم المشروع:", "name"),
            ("نوع المشروع:", "type"),
            ("الموقع:", "location"),
            ("الجهة الطالبة:", "client"),
            ("الحالة:", "status")
        ]
        
        entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(dialog, text=label).grid(row=i, column=0, sticky="e", padx=10, pady=10)
            
            if key == "type":
                entry = ttk.Combobox(dialog, values=["أسفلت", "أعمال ترابية", "كهرباء", "أرصفة"])
                entry.set("أسفلت")
            elif key == "status":
                entry = ttk.Combobox(dialog, values=["تقديم عرض", "مقبول", "جاري التنفيذ", "مكتمل"])
                entry.set("تقديم عرض")
            else:
                entry = tk.Entry(dialog, width=30)
            
            entry.grid(row=i, column=1, padx=10, pady=10)
            entries[key] = entry
        
        # ملاحظات
        tk.Label(dialog, text="ملاحظات:").grid(row=len(fields), column=0, sticky="ne", padx=10, pady=10)
        notes_text = tk.Text(dialog, width=30, height=5)
        notes_text.grid(row=len(fields), column=1, padx=10, pady=10)
        
        def save_project():
            try:
                self.cursor.execute('''
                    INSERT INTO projects (name, type, location, client, status, created_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entries['name'].get(),
                    entries['type'].get(),
                    entries['location'].get(),
                    entries['client'].get(),
                    entries['status'].get(),
                    datetime.now().strftime("%Y-%m-%d"),
                    notes_text.get("1.0", "end-1c")
                ))
                
                self.conn.commit()
                self.refresh_projects()
                dialog.destroy()
                messagebox.showinfo("نجاح", "تم إنشاء المشروع بنجاح!")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}")
        
        tk.Button(dialog, text="💾 حفظ المشروع", command=save_project,
                 bg=self.colors['success'], fg="white").grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
    
    def show_project_details(self):
        """عرض تفاصيل المشروع"""
        selected = self.projects_tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "يرجى اختيار مشروع")
            return
        
        item = self.projects_tree.item(selected[0])
        project_id = item['values'][0]
        
        # فتح نافذة التفاصيل
        dialog = tk.Toplevel(self.root)
        dialog.title("تفاصيل المشروع")
        dialog.geometry("600x500")
        
        # جلب بيانات المشروع
        self.cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project = self.cursor.fetchone()
        
        # عرض البيانات
        info_text = f"""
        اسم المشروع: {project[1]}
        نوع المشروع: {project[2]}
        الموقع: {project[3]}
        الجهة الطالبة: {project[4]}
        الحالة: {project[5]}
        التكلفة الإجمالية: {project[6]:,.0f} ريال
        تاريخ الإنشاء: {project[7]}
        
        ملاحظات:
        {project[8] if project[8] else "لا توجد ملاحظات"}
        """
        
        tk.Label(dialog, text=info_text, font=("Arial", 11), justify="left").pack(padx=20, pady=20)
    
    def delete_project(self):
        """حذف مشروع"""
        selected = self.projects_tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "يرجى اختيار مشروع للحذف")
            return
        
        item = self.projects_tree.item(selected[0])
        project_name = item['values'][1]
        
        if messagebox.askyesno("تأكيد", f"هل تريد حذف المشروع '{project_name}'؟"):
            try:
                project_id = item['values'][0]
                self.cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                self.cursor.execute("DELETE FROM project_items WHERE project_id = ?", (project_id,))
                self.conn.commit()
                self.refresh_projects()
                messagebox.showinfo("نجاح", "تم حذف المشروع بنجاح!")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}")
    
    # ===== دوال التقدير =====
    def add_estimation_item(self):
        """إضافة بند للتقدير"""
        item_name = self.item_name_entry.get()
        category = self.category_var.get()
        quantity = self.quantity_entry.get()
        unit = self.unit_entry.get()
        unit_price = self.unit_price_entry.get()
        
        if not item_name or not quantity or not unit_price:
            messagebox.showwarning("تحذير", "يرجى ملء جميع الحقول")
            return
        
        try:
            quantity = float(quantity)
            unit_price = float(unit_price)
            total_price = quantity * unit_price
            
            # إضافة البند للشجرة
            self.estimation_tree.insert("", "end", values=(
                item_name, category, f"{quantity:,.2f}", unit, f"{unit_price:,.2f}", f"{total_price:,.2f}"
            ))
            
            # تحديث الإجماليات
            self.update_totals()
            
            # مسح الحقول
            self.item_name_entry.delete(0, tk.END)
            self.quantity_entry.delete(0, tk.END)
            self.quantity_entry.insert(0, "1")
            self.unit_price_entry.delete(0, tk.END)
            self.unit_price_entry.insert(0, "0")
            
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال قيم رقمية صحيحة")
    
    def use_template(self):
        """استخدام قالب جاهز"""
        dialog = tk.Toplevel(self.root)
        dialog.title("اختر قالب")
        dialog.geometry("300x200")
        
        tk.Label(dialog, text="اختر نوع العمل:", font=("Arial", 12, "bold")).pack(pady=10)
        
        for template_name in self.templates.keys():
            btn = tk.Button(dialog, text=template_name, width=20,
                          command=lambda name=template_name: self.load_template(name, dialog))
            btn.pack(pady=5)
    
    def load_template(self, template_name, dialog):
        """تحميل قالب"""
        template = self.templates[template_name]
        
        for item in template['items']:
            # البحث عن السعر في قاعدة البيانات
            self.cursor.execute('''
                SELECT price FROM prices WHERE item_name LIKE ? ORDER BY date DESC LIMIT 1
            ''', (f"%{item['name']}%",))
            
            result = self.cursor.fetchone()
            unit_price = result[0] if result else 0
            
            # إضافة البند
            self.estimation_tree.insert("", "end", values=(
                item['name'], item['category'], "1.00", item['unit'], f"{unit_price:,.2f}", f"{unit_price:,.2f}"
            ))
        
        self.update_totals()
        dialog.destroy()
        messagebox.showinfo("تم", f"تم تحميل قالب {template_name}")
    
    def update_totals(self):
        """تحديث الإجماليات"""
        material_total = 0
        labor_total = 0
        equipment_total = 0
        
        for item in self.estimation_tree.get_children():
            values = self.estimation_tree.item(item)['values']
            category = values[1]
            total = float(values[5].replace(',', ''))
            
            if category == "مواد":
                material_total += total
            elif category == "عمالة":
                labor_total += total
            elif category == "معدات":
                equipment_total += total
        
        grand_total = material_total + labor_total + equipment_total
        
        self.material_total_label.config(text=f"{material_total:,.2f} ريال")
        self.labor_total_label.config(text=f"{labor_total:,.2f} ريال")
        self.grand_total_label.config(text=f"{grand_total:,.2f} ريال")
    
    def clear_estimation(self):
        """مسح جميع بنود التقدير"""
        if messagebox.askyesno("تأكيد", "هل تريد مسح جميع البنود؟"):
            for item in self.estimation_tree.get_children():
                self.estimation_tree.delete(item)
            
            self.update_totals()
    
    def save_estimation(self):
        """حفظ التقدير"""
        if not self.estimation_tree.get_children():
            messagebox.showwarning("تحذير", "لا توجد بنود لحفظها")
            return
        
        # اختيار مشروع للحفظ
        project_dialog = tk.Toplevel(self.root)
        project_dialog.title("اختر مشروع")
        project_dialog.geometry("400x300")
        
        tk.Label(project_dialog, text="اختر مشروع لحفظ التقدير:", font=("Arial", 12, "bold")).pack(pady=10)
        
        # جلب المشاريع
        self.cursor.execute("SELECT id, name FROM projects ORDER BY created_date DESC")
        projects = self.cursor.fetchall()
        
        project_var = tk.StringVar()
        
        for project_id, project_name in projects:
            rb = tk.Radiobutton(project_dialog, text=project_name, variable=project_var, value=project_id)
            rb.pack(anchor="w", padx=20)
        
        def confirm_save():
            if not project_var.get():
                messagebox.showwarning("تحذير", "يرجى اختيار مشروع")
                return
            
            project_id = int(project_var.get())
            
            # حذف البنود القديمة للمشروع
            self.cursor.execute("DELETE FROM project_items WHERE project_id = ?", (project_id,))
            
            # إضافة البنود الجديدة
            for item in self.estimation_tree.get_children():
                values = self.estimation_tree.item(item)['values']
                
                self.cursor.execute('''
                    INSERT INTO project_items (project_id, item_name, category, quantity, unit, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_id,
                    values[0],
                    values[1],
                    float(values[2].replace(',', '')),
                    values[3],
                    float(values[4].replace(',', '')),
                    float(values[5].replace(',', ''))
                ))
            
            # حساب التكلفة الإجمالية
            total_cost = sum(float(self.estimation_tree.item(item)['values'][5].replace(',', ''))
                           for item in self.estimation_tree.get_children())
            
            # تحديث تكلفة المشروع
            self.cursor.execute('''
                UPDATE projects SET total_cost = ? WHERE id = ?
            ''', (total_cost, project_id))
            
            self.conn.commit()
            project_dialog.destroy()
            self.clear_estimation()
            self.refresh_projects()
            
            messagebox.showinfo("نجاح", f"تم حفظ التقدير بنجاح!\nالتكلفة الإجمالية: {total_cost:,.2f} ريال")
        
        tk.Button(project_dialog, text="💾 حفظ", command=confirm_save,
                 bg=self.colors['success'], fg="white").pack(pady=20)
    
    # ===== دوال التقارير =====
    def generate_report(self):
        """توليد تقرير"""
        report_type = self.report_type.get()
        
        if report_type == "تقرير تكاليف":
            self.generate_cost_report()
        elif report_type == "مقارنة أسعار":
            self.generate_price_comparison()
        elif report_type == "ملخص المشاريع":
            self.generate_projects_summary()
    
    def generate_cost_report(self):
        """توليد تقرير تكاليف"""
        self.report_text.delete(1.0, tk.END)
        
        report = "=" * 60 + "\n"
        report += " " * 15 + "تقرير تكاليف المشاريع\n"
        report += "=" * 60 + "\n\n"
        
        # جلب المشاريع في النطاق الزمني
        from_date = self.from_date.get()
        to_date = self.to_date.get()
        
        self.cursor.execute('''
            SELECT p.name, p.type, p.location, p.status, p.total_cost, p.created_date,
                   COUNT(i.id) as items_count
            FROM projects p
            LEFT JOIN project_items i ON p.id = i.project_id
            WHERE p.created_date BETWEEN ? AND ?
            GROUP BY p.id
            ORDER BY p.created_date DESC
        ''', (from_date, to_date))
        
        projects = self.cursor.fetchall()
        
        if not projects:
            report += "لا توجد مشاريع في النطاق الزمني المحدد\n"
        else:
            total_all_projects = 0
            
            for project in projects:
                report += f"المشروع: {project[0]}\n"
                report += f"النوع: {project[1]} | الموقع: {project[2]}\n"
                report += f"الحالة: {project[3]} | تاريخ الإنشاء: {project[5]}\n"
                report += f"عدد البنود: {project[6]} | التكلفة: {project[4]:,.0f} ريال\n"
                report += "-" * 40 + "\n"
                
                total_all_projects += project[4] if project[4] else 0
            
            report += f"\n{'='*60}\n"
            report += f"إجمالي تكاليف جميع المشاريع: {total_all_projects:,.0f} ريال\n"
        
        report += f"\nتاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += "=" * 60
        
        self.report_text.insert(1.0, report)
    
    def generate_price_comparison(self):
        """توليد مقارنة أسعار"""
        self.report_text.delete(1.0, tk.END)
        
        report = "=" * 60 + "\n"
        report += " " * 15 + "مقارنة أسعار الموردين\n"
        report += "=" * 60 + "\n\n"
        
        # جلب المواد والأسعار
        self.cursor.execute('''
            SELECT p.item_name, p.category, p.unit, p.price, s.name, p.date
            FROM prices p
            JOIN suppliers s ON p.supplier_id = s.id
            ORDER BY p.item_name, p.price
        ''')
        
        prices = self.cursor.fetchall()
        
        if not prices:
            report += "لا توجد أسعار مسجلة\n"
        else:
            current_item = None
            
            for price in prices:
                if price[0] != current_item:
                    if current_item:
                        report += "-" * 40 + "\n"
                    report += f"\nالمادة: {price[0]} ({price[1]})\n"
                    current_item = price[0]
                
                report += f"  • {price[4]}: {price[3]:,.0f} ريال لل{price[2]} (آخر تحديث: {price[5]})\n"
        
        report += f"\nتاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += "=" * 60
        
        self.report_text.insert(1.0, report)
    
    def generate_projects_summary(self):
        """توليد ملخص المشاريع"""
        self.report_text.delete(1.0, tk.END)
        
        report = "=" * 60 + "\n"
        report += " " * 15 + "ملخص المشاريع\n"
        report += "=" * 60 + "\n\n"
        
        # إحصائيات حسب النوع
        self.cursor.execute('''
            SELECT type, COUNT(*) as count, SUM(total_cost) as total
            FROM projects
            GROUP BY type
        ''')
        
        stats = self.cursor.fetchall()
        
        report += "إحصائيات حسب نوع المشروع:\n"
        report += "-" * 40 + "\n"
        
        for stat in stats:
            report += f"{stat[0]}: {stat[1]} مشروع - {stat[2]:,.0f} ريال\n"
        
        report += "\n" + "=" * 40 + "\n\n"
        
        # إحصائيات حسب الحالة
        self.cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM projects
            GROUP BY status
        ''')
        
        status_stats = self.cursor.fetchall()
        
        report += "إحصائيات حسب الحالة:\n"
        report += "-" * 40 + "\n"
        
        for stat in status_stats:
            report += f"{stat[0]}: {stat[1]} مشروع\n"
        
        report += f"\nتاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += "=" * 60
        
        self.report_text.insert(1.0, report)
    
    def save_report_txt(self):
        """حفظ التقرير كملف نصي"""
        report_text = self.report_text.get(1.0, tk.END)
        
        if not report_text.strip():
            messagebox.showwarning("تحذير", "لا يوجد تقرير لحفظه")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("ملفات نصية", "*.txt"), ("جميع الملفات", "*.*")],
            initialfile=f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                messagebox.showinfo("نجاح", f"تم حفظ التقرير في:\n{filename}")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ في الحفظ: {e}")
    
    # ===== دوال عامة =====
    def new_project(self):
        """مشروع جديد"""
        self.notebook.select(1)  # تبويب المشاريع
        self.new_project_dialog()
    
    def open_project(self):
        """فتح مشروع"""
        messagebox.showinfo("قريباً", "هذه الميزة قيد التطوير")
    
    def save_project(self):
        """حفظ مشروع"""
        messagebox.showinfo("قريباً", "المشاريع تحفظ تلقائياً عند إنشائها")
    
    def export_to_excel(self):
        """تصدير لـ Excel"""
        messagebox.showinfo("قريباً", "هذه الميزة قيد التطوير")
    
    def print_report(self):
        """طباعة التقرير"""
        messagebox.showinfo("قريباً", "هذه الميزة قيد التطوير")
    
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        try:
            backup_file = f"backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            # إغلاق الاتصال الحالي
            self.conn.close()
            
            # نسخ قاعدة البيانات
            import shutil
            shutil.copy2('data/estimation.db', backup_file)
            
            # إعادة فتح الاتصال
            self.conn = sqlite3.connect('data/estimation.db')
            self.cursor = self.conn.cursor()
            
            messagebox.showinfo("نجاح", f"تم إنشاء نسخة احتياطية في:\n{backup_file}")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ في النسخ الاحتياطي: {e}")
    
    def restore_backup(self):
        """استعادة نسخة احتياطية"""
        filename = filedialog.askopenfilename(
            filetypes=[("ملفات قاعدة بيانات", "*.db"), ("جميع الملفات", "*.*")]
        )
        
        if filename:
            if messagebox.askyesno("تأكيد", "هل تريد استعادة النسخة الاحتياطية؟\nسيتم فقدان البيانات الحالية!"):
                try:
                    # إغلاق الاتصال
                    self.conn.close()
                    
                    # استعادة النسخة
                    import shutil
                    shutil.copy2(filename, 'data/estimation.db')
                    
                    # إعادة فتح الاتصال
                    self.conn = sqlite3.connect('data/estimation.db')
                    self.cursor = self.conn.cursor()
                    
                    # تحديث الواجهة
                    self.refresh_suppliers()
                    self.refresh_projects()
                    
                    messagebox.showinfo("نجاح", "تم استعادة النسخة الاحتياطية بنجاح!")
                except Exception as e:
                    messagebox.showerror("خطأ", f"حدث خطأ في الاستعادة: {e}")
    
    def open_settings(self):
        """فتح الإعدادات"""
        messagebox.showinfo("قريباً", "هذه الميزة قيد التطوير")
    
    def show_help(self):
        """عرض دليل المستخدم"""
        help_text = """
        دليل استخدام نظام تقدير التكاليف:
        
        1. الصفحة الرئيسية:
           - نظرة عامة على النظام
           - إحصائيات سريعة
           - أزرار سريعة للوظائف الرئيسية
        
        2. الموردون:
           - إضافة موردين جدد
           - تعديل بيانات الموردين
           - حذف الموردين
           - تحديث القائمة
        
        3. المشاريع:
           - إنشاء مشاريع جديدة
           - عرض تفاصيل المشروع
           - حذف المشاريع
        
        4. التقدير:
           - إضافة بنود تكاليف يدوياً
           - استخدام قوالب جاهزة
           - حساب الإجماليات
           - حفظ التقدير لمشروع
        
        5. التقارير:
           - توليد تقارير التكاليف
           - مقارنة أسعار الموردين
           - ملخص المشاريع
           - حفظ التقارير كملفات نصية
        
        للتطوير المستقبلي:
        - تصدير لـ Excel
        - طباعة التقارير
        - المزيد من القوالب
        - إدارة المهام
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("دليل المستخدم")
        help_window.geometry("600x500")
        
        text_widget = tk.Text(help_window, wrap="word", font=("Arial", 11))
        text_widget.insert(1.0, help_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Button(help_window, text="إغلاق", command=help_window.destroy,
                 bg=self.colors['primary'], fg="white").pack(pady=10)
    
    def show_about(self):
        """عرض معلومات عن التطبيق"""
        about_text = """
        نظام تقدير تكاليف المشاريع الحكومية
        
        الإصدار: 1.0.0
        التاريخ: 2024
        
        المميزات:
        • إدارة قاعدة بيانات الموردين والأسعار
        • تقدير تكاليف مشاريع الأسفلت والأعمال الترابية
        • إدارة مشاريع الكهرباء والأرصفة
        • توليد تقارير تفصيلية
        • مقارنة أسعار الموردين
        
        صمم خصيصاً لمهندسي التكاليف والعروض
        في المشاريع الحكومية
        
        © 2024 - جميع الحقوق محفوظة
        """
        
        messagebox.showinfo("حول التطبيق", about_text)

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    root = tk.Tk()
    
    # إضافة أيقونة إذا كانت موجودة
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
    
    # تشغيل التطبيق
    app = EstimationApp(root)
    
    # تنسيق الخط للغة العربية
    try:
        import tkinter.font as tkFont
        font = tkFont.Font(family="Arial", size=10)
        root.option_add("*Font", font)
    except:
        pass
    
    # تشغيل الواجهة
    root.mainloop()

if __name__ == "__main__":
    main()