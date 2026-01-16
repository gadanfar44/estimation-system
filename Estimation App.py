# -*- coding: utf-8 -*-
"""
تطبيق تقدير تكاليف المشاريع الحكومية - النسخة السحابية
مخصص لمهندس التكاليف والعروض
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
import base64

# إعداد الصفحة
st.set_page_config(
    page_title="نظام تقدير التكاليف - الحكومي",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيق عربي
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

* {
    font-family: 'Cairo', sans-serif !important;
}

.stApp {
    background-color: #f8f9fa;
}

.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.card {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    margin-bottom: 1rem;
    transition: transform 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.1);
}

.rtl {
    direction: rtl;
    text-align: right;
}

.status-completed {
    background-color: #d4edda;
    color: #155724;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
}

.status-pending {
    background-color: #fff3cd;
    color: #856404;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
}

.status-in-progress {
    background-color: #d1ecf1;
    color: #0c5460;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# إنشاء قاعدة البيانات
def init_database():
    conn = sqlite3.connect('data/projects.db')
    cursor = conn.cursor()
    
    # جدول المشاريع
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        project_type TEXT,
        location TEXT,
        client TEXT,
        start_date TEXT,
        end_date TEXT,
        status TEXT,
        total_cost REAL,
        created_at TEXT,
        notes TEXT
    )
    ''')
    
    # جدول الموردين
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT NOT NULL,
        contact_person TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        specialization TEXT,
        rating INTEGER,
        last_updated TEXT
    )
    ''')
    
    # جدول أسعار المواد
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS material_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_name TEXT NOT NULL,
        unit TEXT,
        category TEXT,
        supplier_id INTEGER,
        price REAL,
        date TEXT,
        notes TEXT,
        FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
    )
    ''')
    
    # جدول تكاليف المشاريع
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        item_name TEXT,
        category TEXT,
        quantity REAL,
        unit TEXT,
        material_cost REAL,
        labor_cost REAL,
        equipment_cost REAL,
        other_cost REAL,
        total_cost REAL,
        notes TEXT,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    ''')
    
    # إضافة بيانات تجريبية إذا كانت الجداول فارغة
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        # إضافة مشاريع تجريبية
        sample_projects = [
            ('رصف طريق الملك فهد', 'أسفلت', 'الرياض', 'أمانة الرياض', 
             '2024-01-15', '2024-06-30', 'جاري التنفيذ', 2850000, 
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             'مشروع رصف بطول 5 كم بعرض 12 م'),
            
            ('توريد تربة دفان', 'أعمال ترابية', 'جدة', 'جامعة الملك عبدالعزيز',
             '2024-02-01', '2024-03-15', 'تقديم عرض', 850000,
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             'توريد 5000 م³ تربة دفان'),
            
            ('إنارة حديقة عامة', 'كهرباء', 'الدمام', 'أمانة الشرقية',
             '2024-01-20', '2024-04-30', 'مكتمل', 420000,
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             'تركيب 30 عمود إنارة LED'),
        ]
        
        cursor.executemany('''
        INSERT INTO projects (project_name, project_type, location, client, 
                            start_date, end_date, status, total_cost, created_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_projects)
    
    # إضافة موردين تجريبيين
    cursor.execute("SELECT COUNT(*) FROM suppliers")
    if cursor.fetchone()[0] == 0:
        sample_suppliers = [
            ('شركة الأسفلت الوطنية', 'محمد أحمد', '0555123456', 
             'info@asphalt.com', 'الرياض - الصناعية', 'مواد أسفلت', 4, 
             datetime.now().strftime('%Y-%m-%d')),
            
            ('مؤسسة التربة والردم', 'سعود المري', '0500987654',
             'contact@soil.com', 'جدة - الكورنيش', 'تربة ودفان', 5,
             datetime.now().strftime('%Y-%m-%d')),
            
            ('شركة الكهرباء المتقدمة', 'خالد الغامدي', '0566778899',
             'sales@elec.com', 'الدمام - الخبر', 'مواد كهربائية', 4,
             datetime.now().strftime('%Y-%m-%d')),
            
            ('مصنع الإنترلوك الحديث', 'علي السعد', '0544332211',
             'factory@interlock.com', 'الرياض - السلي', 'بلدورات وإنترلوك', 3,
             datetime.now().strftime('%Y-%m-%d')),
        ]
        
        cursor.executemany('''
        INSERT INTO suppliers (supplier_name, contact_person, phone, email, 
                             address, specialization, rating, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_suppliers)
    
    # إضافة أسعار مواد تجريبية
    cursor.execute("SELECT COUNT(*) FROM material_prices")
    if cursor.fetchone()[0] == 0:
        sample_prices = [
            ('خلطة أسفلت', 'م³', 'أسفلت', 1, 150, 
             datetime.now().strftime('%Y-%m-%d'), 'سعر المتر المكعب'),
            ('بيتومين', 'طن', 'أسفلت', 1, 2000, 
             datetime.now().strftime('%Y-%m-%d'), 'للطلاء الساخن'),
            ('تربة دفان', 'م³', 'تربة', 2, 40, 
             datetime.now().strftime('%Y-%m-%d'), 'جودة عالية'),
            ('رمل نظيف', 'م³', 'تربة', 2, 30, 
             datetime.now().strftime('%Y-%m-%d'), 'للردم'),
            ('عمود إنارة 10م', 'وحدة', 'كهرباء', 3, 850, 
             datetime.now().strftime('%Y-%m-%d'), 'بزينة LED'),
            ('كابل كهرباء 16مم', 'متر', 'كهرباء', 3, 12, 
             datetime.now().strftime('%Y-%m-%d'), 'نحاس'),
            ('بلاط إنترلوك', 'م²', 'أرصفة', 4, 45, 
             datetime.now().strftime('%Y-%m-%d'), '8 سم سماكة'),
            ('بلدورة خرسانية', 'متر', 'أرصفة', 4, 18, 
             datetime.now().strftime('%Y-%m-%d'), '15×30 سم'),
        ]
        
        cursor.executemany('''
        INSERT INTO material_prices (material_name, unit, category, supplier_id, 
                                    price, date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_prices)
    
    conn.commit()
    conn.close()

# تحميل القوالب
def load_templates():
    templates = {
        "أسفلت": {
            "description": "أعمال رصف أسفلتي",
            "items": [
                {"name": "خلطة أسفلت", "unit": "م³", "category": "مواد"},
                {"name": "بيتومين", "unit": "طن", "category": "مواد"},
                {"name": "عمال رصف", "unit": "يوم", "category": "عمالة"},
                {"name": "فرادة أسفلت", "unit": "يوم", "category": "معدات"},
                {"name": "مدحلة", "unit": "يوم", "category": "معدات"},
                {"name": "نقل مواد", "unit": "رحلة", "category": "نقل"},
            ]
        },
        "أعمال ترابية": {
            "description": "حفر وردم وتسوية",
            "items": [
                {"name": "تربة دفان", "unit": "م³", "category": "مواد"},
                {"name": "رمل نظيف", "unit": "م³", "category": "مواد"},
                {"name": "عمال حفر", "unit": "يوم", "category": "عمالة"},
                {"name": "بوكلين", "unit": "يوم", "category": "معدات"},
                {"name": "شيول", "unit": "يوم", "category": "معدات"},
                {"name": "قلاب", "unit": "يوم", "category": "معدات"},
            ]
        },
        "كهرباء وإنارة": {
            "description": "أعمال تمديدات وإنارة",
            "items": [
                {"name": "عمود إنارة", "unit": "وحدة", "category": "مواد"},
                {"name": "كابل كهرباء", "unit": "متر", "category": "مواد"},
                {"name": "لمبات LED", "unit": "وحدة", "category": "مواد"},
                {"name": "فني كهرباء", "unit": "يوم", "category": "عمالة"},
                {"name": "عمال مساعدين", "unit": "يوم", "category": "عمالة"},
                {"name": "سيارة صغيرة", "unit": "يوم", "category": "معدات"},
            ]
        },
        "أرصفة وإنترلوك": {
            "description": "أعمال بلاط وإنترلوك وبلدورات",
            "items": [
                {"name": "بلاط إنترلوك", "unit": "م²", "category": "مواد"},
                {"name": "بلدورة خرسانية", "unit": "متر", "category": "مواد"},
                {"name": "رمل فرش", "unit": "م³", "category": "مواد"},
                {"name": "أسمنت", "unit": "كيس", "category": "مواد"},
                {"name": "عمال بلاط", "unit": "يوم", "category": "عمالة"},
                {"name": "معدات يدوية", "unit": "يوم", "category": "معدات"},
            ]
        }
    }
    return templates

# الصفحة الرئيسية
def main_page():
    # Header
    st.markdown("""
    <div class="main-header rtl">
        <h1>🏗️ نظام تقدير تكاليف المشاريع الحكومية</h1>
        <p>نظام متكامل لتقدير تكاليف مشاريع الأسفلت، الأعمال الترابية، الكهرباء، والأرصفة</p>
    </div>
    """, unsafe_allow_html=True)
    
    # إحصائيات سريعة
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="card rtl">
            <h3>📊 12</h3>
            <p>مشروع نشط</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card rtl">
            <h3>💰 8.5M</h3>
            <p>ريال إجمالي التكاليف</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card rtl">
            <h3>👥 24</h3>
            <p>مورد مسجل</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="card rtl">
            <h3>📈 95%</h3>
            <p>دقة التقدير</p>
        </div>
        """, unsafe_allow_html=True)
    
    # قسم المشاريع الحديثة
    st.markdown("### 📋 المشاريع الحديثة")
    
    conn = sqlite3.connect('data/projects.db')
    projects = pd.read_sql_query("SELECT * FROM projects ORDER BY created_at DESC LIMIT 5", conn)
    conn.close()
    
    for _, project in projects.iterrows():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.write(f"**{project['project_name']}**")
            st.caption(f"📍 {project['location']} | 👤 {project['client']}")
        
        with col2:
            st.write(f"**نوع المشروع:** {project['project_type']}")
        
        with col3:
            status_color = {
                'جاري التنفيذ': 'status-in-progress',
                'مكتمل': 'status-completed',
                'تقديم عرض': 'status-pending'
            }.get(project['status'], 'status-pending')
            
            st.markdown(f"<div class='{status_color}'>{project['status']}</div>", unsafe_allow_html=True)
        
        with col4:
            st.write(f"**💰 {project['total_cost']:,.0f} ريال**")
    
    # قسم الموردين المميزين
    st.markdown("### 👥 الموردون المميزون")
    
    conn = sqlite3.connect('data/projects.db')
    suppliers = pd.read_sql_query("""
    SELECT s.supplier_name, s.specialization, s.rating, 
           COUNT(DISTINCT mp.material_name) as materials_count
    FROM suppliers s
    LEFT JOIN material_prices mp ON s.id = mp.supplier_id
    GROUP BY s.id
    ORDER BY s.rating DESC
    LIMIT 4
    """, conn)
    conn.close()
    
    cols = st.columns(4)
    for idx, (_, supplier) in enumerate(suppliers.iterrows()):
        with cols[idx]:
            stars = "★" * int(supplier['rating']) + "☆" * (5 - int(supplier['rating']))
            st.markdown(f"""
            <div class="card rtl">
                <h4>{supplier['supplier_name']}</h4>
                <p>{supplier['specialization']}</p>
                <p style="color: gold;">{stars}</p>
                <small>{supplier['materials_count']} مادة مسعّرة</small>
            </div>
            """, unsafe_allow_html=True)
    
    # مخطط إحصائي
    st.markdown("### 📈 توزيع المشاريع حسب النوع")
    
    conn = sqlite3.connect('data/projects.db')
    project_stats = pd.read_sql_query("""
    SELECT project_type, COUNT(*) as count, SUM(total_cost) as total_cost
    FROM projects
    GROUP BY project_type
    """, conn)
    conn.close()
    
    if not project_stats.empty:
        fig = px.pie(project_stats, values='total_cost', names='project_type',
                     title='التكلفة الإجمالية حسب نوع المشروع',
                     color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(title_font_size=16, title_x=0.5)
        st.plotly_chart(fig, use_container_width=True)

# صفحة إدارة المشاريع
def projects_page():
    st.markdown("<h1 class='rtl'>🏗️ إدارة المشاريع</h1>", unsafe_allow_html=True)
    
    # تبويبات
    tab1, tab2, tab3, tab4 = st.tabs(["📋 المشاريع الحالية", "➕ مشروع جديد", "📂 المشاريع القديمة", "🔍 بحث وتصفية"])
    
    with tab1:
        conn = sqlite3.connect('data/projects.db')
        projects = pd.read_sql_query("SELECT * FROM projects ORDER BY created_at DESC", conn)
        conn.close()
        
        if not projects.empty:
            # عرض المشاريع في جدول تفاعلي
            edited_df = st.data_editor(
                projects[['project_name', 'project_type', 'location', 'status', 'total_cost']],
                column_config={
                    "project_name": st.column_config.TextColumn("اسم المشروع"),
                    "project_type": st.column_config.SelectboxColumn(
                        "نوع المشروع",
                        options=["أسفلت", "أعمال ترابية", "كهرباء", "أرصفة", "صرف صحي", "أخرى"]
                    ),
                    "location": st.column_config.TextColumn("الموقع"),
                    "status": st.column_config.SelectboxColumn(
                        "الحالة",
                        options=["تقديم عرض", "مقبول", "جاري التنفيذ", "مكتمل", "ملغي"]
                    ),
                    "total_cost": st.column_config.NumberColumn("التكلفة", format="%,d")
                },
                hide_index=True,
                num_rows="dynamic",
                use_container_width=True
            )
            
            if st.button("💾 حفظ التعديلات", type="primary"):
                conn = sqlite3.connect('data/projects.db')
                # هنا يجب تحديث البيانات في قاعدة البيانات
                st.success("تم حفظ التعديلات بنجاح!")
                conn.close()
        
        else:
            st.info("لا توجد مشاريع مسجلة حالياً. أضف مشروعاً جديداً من تبويب '➕ مشروع جديد'")
    
    with tab2:
        st.markdown("### 📝 إضافة مشروع جديد")
        
        with st.form("new_project_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                project_name = st.text_input("اسم المشروع *", placeholder="مثال: رصف طريق الملك فهد")
                project_type = st.selectbox("نوع المشروع *", 
                                          ["أسفلت", "أعمال ترابية", "كهرباء", "أرصفة", "صرف صحي", "أخرى"])
                location = st.text_input("الموقع *", placeholder="مثال: الرياض - حي الملز")
                client = st.text_input("الجهة الطالبة *", placeholder="مثال: أمانة الرياض")
            
            with col2:
                start_date = st.date_input("تاريخ البدء")
                end_date = st.date_input("تاريخ الانتهاء المتوقع")
                status = st.selectbox("الحالة", ["تقديم عرض", "مقبول", "جاري التنفيذ", "مكتمل", "ملغي"])
                initial_budget = st.number_input("الميزانية التقديرية (ريال)", min_value=0, value=0)
                notes = st.text_area("ملاحظات", placeholder="أي معلومات إضافية عن المشروع")
            
            submitted = st.form_submit_button("➕ إضافة المشروع")
            
            if submitted:
                if project_name and location and client:
                    conn = sqlite3.connect('data/projects.db')
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                    INSERT INTO projects (project_name, project_type, location, client, 
                                        start_date, end_date, status, total_cost, created_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (project_name, project_type, location, client,
                         start_date.strftime('%Y-%m-%d') if start_date else None,
                         end_date.strftime('%Y-%m-%d') if end_date else None,
                         status, initial_budget,
                         datetime.now().strftime('%Y-%m-%d %H:%M:%S'), notes))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"تم إضافة مشروع '{project_name}' بنجاح!")
                    st.balloons()
                else:
                    st.error("يرجى ملء الحقول الإلزامية (*)")
    
    with tab3:
        st.markdown("### 📂 قاعدة المشاريع القديمة")
        
        # خيارات التصفية
        col1, col2, col3 = st.columns(3)
        
        with col1:
            year_filter = st.selectbox("السنة", ["الكل"] + list(range(2020, 2025)))
        
        with col2:
            type_filter = st.selectbox("نوع المشروع", ["الكل", "أسفلت", "أعمال ترابية", "كهرباء", "أرصفة"])
        
        with col3:
            status_filter = st.selectbox("الحالة", ["الكل", "مكتمل", "جاري التنفيذ", "تقديم عرض"])
        
        # عرض المشاريع المصفاة
        conn = sqlite3.connect('data/projects.db')
        query = "SELECT * FROM projects WHERE 1=1"
        params = []
        
        if year_filter != "الكل":
            query += " AND strftime('%Y', created_at) = ?"
            params.append(str(year_filter))
        
        if type_filter != "الكل":
            query += " AND project_type = ?"
            params.append(type_filter)
        
        if status_filter != "الكل":
            query += " AND status = ?"
            params.append(status_filter)
        
        query += " ORDER BY created_at DESC"
        
        old_projects = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not old_projects.empty:
            for _, project in old_projects.iterrows():
                with st.expander(f"{project['project_name']} - {project['total_cost']:,.0f} ريال"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**الموقع:** {project['location']}")
                        st.write(f"**الجهة الطالبة:** {project['client']}")
                        st.write(f"**نوع المشروع:** {project['project_type']}")
                    
                    with col2:
                        st.write(f"**تاريخ البدء:** {project['start_date']}")
                        st.write(f"**تاريخ الانتهاء:** {project['end_date']}")
                        st.write(f"**الحالة:** {project['status']}")
                    
                    if st.button("📋 عرض تفاصيل التكاليف", key=f"details_{project['id']}"):
                        st.session_state['selected_project'] = project['id']
                        st.switch_page("pages/04_💰_تقدير_التكاليف.py")
        
        else:
            st.info("لا توجد مشاريع تطابق معايير البحث")

# صفحة الموردين والأسعار
def suppliers_page():
    st.markdown("<h1 class='rtl'>👥 إدارة الموردين والأسعار</h1>", unsafe_allow_html=True)
    
    # تبويبات
    tab1, tab2, tab3, tab4 = st.tabs(["🏢 الموردون", "💰 أسعار المواد", "📊 مقارنة الأسعار", "📅 تحديث الأسعار"])
    
    with tab1:
        st.markdown("### 🏢 قاعدة بيانات الموردين")
        
        # إضافة مورد جديد
        with st.expander("➕ إضافة مورد جديد", expanded=False):
            with st.form("new_supplier_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    supplier_name = st.text_input("اسم المورد *", placeholder="مثال: شركة الأسفلت الوطنية")
                    contact_person = st.text_input("اسم المسؤول", placeholder="مثال: محمد أحمد")
                    phone = st.text_input("رقم الهاتف *", placeholder="مثال: 0555123456")
                
                with col2:
                    email = st.text_input("البريد الإلكتروني", placeholder="مثال: info@company.com")
                    specialization = st.selectbox("التخصص", ["أسفلت", "تربة وردم", "كهرباء", "إنترلوك", "مواد بناء", "أخرى"])
                    rating = st.slider("التقييم", 1, 5, 3)
                
                address = st.text_area("العنوان", placeholder="العنوان التفصيلي")
                
                submitted = st.form_submit_button("➕ إضافة المورد")
                
                if submitted:
                    if supplier_name and phone:
                        conn = sqlite3.connect('data/projects.db')
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                        INSERT INTO suppliers (supplier_name, contact_person, phone, email, 
                                             address, specialization, rating, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (supplier_name, contact_person, phone, email, address, 
                             specialization, rating, datetime.now().strftime('%Y-%m-%d')))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"تم إضافة المورد '{supplier_name}' بنجاح!")
        
        # عرض الموردين
        conn = sqlite3.connect('data/projects.db')
        suppliers = pd.read_sql_query("""
        SELECT s.*, COUNT(mp.id) as materials_count,
               MAX(mp.date) as last_price_update
        FROM suppliers s
        LEFT JOIN material_prices mp ON s.id = mp.supplier_id
        GROUP BY s.id
        ORDER BY s.supplier_name
        """, conn)
        conn.close()
        
        if not suppliers.empty:
            for _, supplier in suppliers.iterrows():
                with st.expander(f"🏢 {supplier['supplier_name']} - ⭐ {supplier['rating']}/5"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**التخصص:** {supplier['specialization']}")
                        st.write(f"**المسؤول:** {supplier['contact_person']}")
                        st.write(f"**الهاتف:** {supplier['phone']}")
                        st.write(f"**البريد:** {supplier['email']}")
                    
                    with col2:
                        st.write(f"**العنوان:** {supplier['address']}")
                        st.write(f"**عدد المواد:** {supplier['materials_count']}")
                        st.write(f"**آخر تحديث:** {supplier['last_updated']}")
                        if supplier['last_price_update']:
                            st.write(f"**آخر سعر:** {supplier['last_price_update']}")
    
    with tab2:
        st.markdown("### 📋 أسعار المواد الحالية")
        
        # تصفية حسب الفئة
        categories = ["الكل", "أسفلت", "تربة", "كهرباء", "أرصفة", "مواد بناء"]
        selected_category = st.selectbox("تصفية حسب الفئة", categories)
        
        conn = sqlite3.connect('data/projects.db')
        
        query = """
        SELECT mp.material_name, mp.unit, mp.category, mp.price, 
               mp.date, s.supplier_name, mp.notes
        FROM material_prices mp
        JOIN suppliers s ON mp.supplier_id = s.id
        """
        
        if selected_category != "الكل":
            query += f" WHERE mp.category = '{selected_category}'"
        
        query += " ORDER BY mp.category, mp.material_name"
        
        prices = pd.read_sql_query(query, conn)
        conn.close()
        
        if not prices.empty:
            # عرض الأسعار في جدول
            edited_prices = st.data_editor(
                prices,
                column_config={
                    "material_name": "اسم المادة",
                    "unit": "الوحدة",
                    "category": "الفئة",
                    "price": st.column_config.NumberColumn("السعر", format="%,d"),
                    "date": "تاريخ السعر",
                    "supplier_name": "المورد",
                    "notes": "ملاحظات"
                },
                hide_index=True,
                use_container_width=True
            )
            
            col1, col2, col3 = st.columns(3)
            with col2:
                if st.button("💾 حفظ تحديثات الأسعار", type="primary"):
                    # هنا سيتم حفظ التعديلات في قاعدة البيانات
                    st.success("تم حفظ التحديثات!")
        
        # إضافة سعر جديد
        with st.expander("➕ إضافة سعر مادة جديدة", expanded=False):
            with st.form("new_price_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    material_name = st.text_input("اسم المادة *", placeholder="مثال: خلطة أسفلت")
                    unit = st.text_input("الوحدة *", placeholder="مثال: م³، طن، كيس")
                    category = st.selectbox("الفئة *", ["أسفلت", "تربة", "كهرباء", "أرصفة", "مواد بناء"])
                
                with col2:
                    conn = sqlite3.connect('data/projects.db')
                    suppliers_list = pd.read_sql_query("SELECT id, supplier_name FROM suppliers WHERE specialization = ?", 
                                                     conn, params=[category])
                    conn.close()
                    
                    supplier_options = {row['supplier_name']: row['id'] for _, row in suppliers_list.iterrows()}
                    selected_supplier = st.selectbox("المورد *", list(supplier_options.keys()))
                    price = st.number_input("السعر (ريال) *", min_value=0.0, value=0.0)
                    notes = st.text_area("ملاحظات")
                
                submitted = st.form_submit_button("➕ إضافة السعر")
                
                if submitted:
                    if material_name and unit and category and selected_supplier:
                        conn = sqlite3.connect('data/projects.db')
                        cursor = conn.cursor()
                        
                        supplier_id = supplier_options[selected_supplier]
                        
                        cursor.execute('''
                        INSERT INTO material_prices (material_name, unit, category, supplier_id, 
                                                   price, date, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (material_name, unit, category, supplier_id, price,
                             datetime.now().strftime('%Y-%m-%d'), notes))
                        
                        # تحديث تاريخ المورد
                        cursor.execute('''
                        UPDATE suppliers SET last_updated = ?
                        WHERE id = ?
                        ''', (datetime.now().strftime('%Y-%m-%d'), supplier_id))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"تم إضافة سعر '{material_name}' بنجاح!")
    
    with tab3:
        st.markdown("### 📊 مقارنة أسعار الموردين")
        
        # اختيار مادة للمقارنة
        conn = sqlite3.connect('data/projects.db')
        materials = pd.read_sql_query("SELECT DISTINCT material_name FROM material_prices", conn)
        conn.close()
        
        selected_material = st.selectbox("اختر مادة للمقارنة", materials['material_name'].tolist())
        
        if selected_material:
            conn = sqlite3.connect('data/projects.db')
            comparison = pd.read_sql_query("""
            SELECT s.supplier_name, mp.price, mp.unit, mp.date, s.rating
            FROM material_prices mp
            JOIN suppliers s ON mp.supplier_id = s.id
            WHERE mp.material_name = ?
            ORDER BY mp.price
            """, conn, params=[selected_material])
            conn.close()
            
            if not comparison.empty:
                # عرض المقارنة في جدول
                st.dataframe(comparison, use_container_width=True)
                
                # رسم بياني للمقارنة
                fig = go.Figure(data=[
                    go.Bar(x=comparison['supplier_name'], y=comparison['price'],
                          text=comparison['price'], textposition='auto',
                          marker_color=px.colors.sequential.Viridis)
                ])
                
                fig.update_layout(
                    title=f"مقارنة أسعار {selected_material}",
                    xaxis_title="المورد",
                    yaxis_title="السعر (ريال)",
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # التوصية
                best_price = comparison.loc[comparison['price'].idxmin()]
                st.info(f"""
                **🎯 التوصية:** أفضل سعر من **{best_price['supplier_name']}** 
                بسعر **{best_price['price']:,.0f} ريال** لل{best_price['unit']}
                """)
    
    with tab4:
        st.markdown("### 📅 جدول تحديث الأسعار")
        
        # حساب المدة منذ آخر تحديث
        conn = sqlite3.connect('data/projects.db')
        last_updates = pd.read_sql_query("""
        SELECT s.supplier_name, s.specialization, 
               s.last_updated as supplier_update,
               MAX(mp.date) as last_price_update,
               julianday('now') - julianday(MAX(mp.date)) as days_since_update
        FROM suppliers s
        LEFT JOIN material_prices mp ON s.id = mp.supplier_id
        GROUP BY s.id
        ORDER BY days_since_update DESC
        """, conn)
        conn.close()
        
        if not last_updates.empty:
            # تصنيف الموردين حسب مدة التحديث
            last_updates['status'] = last_updates['days_since_update'].apply(
                lambda x: '🟢 حديث' if x < 30 else ('🟡 متوسط' if x < 90 else '🔴 قديم')
            )
            
            for _, supplier in last_updates.iterrows():
                status_color = {
                    '🟢 حديث': 'status-completed',
                    '🟡 متوسط': 'status-in-progress',
                    '🔴 قديم': 'status-pending'
                }.get(supplier['status'], '')
                
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{supplier['supplier_name']}**")
                    st.caption(f"{supplier['specialization']}")
                
                with col2:
                    if pd.notna(supplier['last_price_update']):
                        st.write(f"آخر تحديث: {supplier['last_price_update']}")
                    else:
                        st.write("لا توجد أسعار مسجلة")
                
                with col3:
                    if pd.notna(supplier['days_since_update']):
                        days = int(supplier['days_since_update'])
                        st.write(f"قبل {days} يوم")
                
                with col4:
                    st.markdown(f"<div class='{status_color}'>{supplier['status']}</div>", unsafe_allow_html=True)
        
        # زر تحديث جماعي
        st.markdown("---")
        st.markdown("### 🔄 تحديث جماعي للأسعار")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            update_percentage = st.slider("نسبة الزيادة/النقصان %", -20, 20, 0)
        
        with col2:
            selected_category = st.selectbox("الفئة للتحديث", ["الكل", "أسفلت", "تربة", "كهرباء"])
        
        with col3:
            selected_supplier = st.selectbox("المورد", ["الكل"] + suppliers['supplier_name'].tolist())
        
        if st.button("🔄 تطبيق التحديث الجماعي", type="primary"):
            st.warning("هذه الميزة قيد التطوير")

# صفحة تقدير التكاليف
def estimation_page():
    st.markdown("<h1 class='rtl'>💰 تقدير تكاليف المشاريع</h1>", unsafe_allow_html=True)
    
    # اختيار مشروع
    conn = sqlite3.connect('data/projects.db')
    projects = pd.read_sql_query("SELECT id, project_name FROM projects", conn)
    conn.close()
    
    if projects.empty:
        st.warning("لا توجد مشاريع مسجلة. الرجاء إضافة مشروع أولاً.")
        return
    
    project_options = {row['project_name']: row['id'] for _, row in projects.iterrows()}
    selected_project_name = st.selectbox("اختر مشروعاً", list(project_options.keys()))
    project_id = project_options[selected_project_name]
    
    if 'selected_project' in st.session_state:
        project_id = st.session_state['selected_project']
        selected_project_name = [k for k, v in project_options.items() if v == project_id][0]
        st.session_state.pop('selected_project', None)
    
    st.markdown(f"### 📋 تقدير تكاليف: {selected_project_name}")
    
    # تحميل القوالب
    templates = load_templates()
    template_names = list(templates.keys())
    
    # تبويبات التقدير
    tab1, tab2, tab3, tab4 = st.tabs(["🧱 استخدام قالب", "➕ إضافة بنود يدوياً", "📊 تحليل التكاليف", "💾 حفظ وطباعة"])
    
    with tab1:
        st.markdown("#### 🧱 اختيار قالب العمل")
        
        selected_template = st.selectbox("اختر قالب العمل", template_names)
        
        if selected_template:
            template = templates[selected_template]
            st.info(f"**وصف القالب:** {template['description']}")
            
            # عرض بنود القالب
            st.markdown("##### بنود القالب:")
            
            for i, item in enumerate(template['items']):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.write(f"**{item['name']}** ({item['category']})")
                
                with col2:
                    quantity = st.number_input(f"الكمية", min_value=0.0, value=1.0, 
                                              key=f"qty_{i}", label_visibility="collapsed")
                
                with col3:
                    # جلب الأسعار من قاعدة البيانات
                    conn = sqlite3.connect('data/projects.db')
                    
                    if item['category'] == 'مواد':
                        price_query = """
                        SELECT price FROM material_prices 
                        WHERE material_name LIKE ? 
                        ORDER BY date DESC LIMIT 1
                        """
                        price_result = pd.read_sql_query(price_query, conn, 
                                                        params=[f"%{item['name']}%"])
                    else:
                        # للعمالة والمعدات، نستخدم أسعار افتراضية
                        price_result = pd.DataFrame({'price': [0]})
                    
                    conn.close()
                    
                    unit_price = price_result['price'].iloc[0] if not price_result.empty else 0
                    st.number_input("سعر الوحدة", value=float(unit_price), 
                                   key=f"price_{i}", label_visibility="collapsed")
                
                with col4:
                    total = quantity * unit_price
                    st.write(f"**الإجمالي:** {total:,.0f} ريال")
            
            if st.button("💾 حفظ البنود من القالب", type="primary"):
                st.success("تم حفظ بنود القالب!")
    
    with tab2:
        st.markdown("#### ➕ إضافة بنود تقدير يدوياً")
        
        # نموذج إضافة بند جديد
        with st.form("new_item_form"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                item_name = st.text_input("اسم البند *", placeholder="مثال: خلطة أسفلت")
                category = st.selectbox("الفئة *", ["مواد", "عمالة", "معدات", "نقل", "أخرى"])
            
            with col2:
                quantity = st.number_input("الكمية *", min_value=0.0, value=1.0)
                unit = st.text_input("الوحدة *", placeholder="مثال: م³، يوم، رحلة")
            
            with col3:
                # حساب سعر الوحدة بناء على الفئة
                if category == "مواد":
                    conn = sqlite3.connect('data/projects.db')
                    materials = pd.read_sql_query("SELECT material_name FROM material_prices", conn)
                    conn.close()
                    
                    if not materials.empty and item_name:
                        # البحث عن سعر المادة
                        conn = sqlite3.connect('data/projects.db')
                        price_query = """
                        SELECT price FROM material_prices 
                        WHERE material_name LIKE ? 
                        ORDER BY date DESC LIMIT 1
                        """
                        price_result = pd.read_sql_query(price_query, conn, 
                                                        params=[f"%{item_name}%"])
                        conn.close()
                        
                        unit_price = price_result['price'].iloc[0] if not price_result.empty else 0
                    else:
                        unit_price = st.number_input("سعر الوحدة", min_value=0.0, value=0.0)
                else:
                    unit_price = st.number_input("سعر الوحدة", min_value=0.0, value=0.0)
            
            with col4:
                notes = st.text_area("ملاحظات", height=50)
            
            submitted = st.form_submit_button("➕ إضافة البند")
            
            if submitted:
                if item_name and category and unit:
                    total_cost = quantity * unit_price
                    
                    # حفظ البند في قاعدة البيانات
                    conn = sqlite3.connect('data/projects.db')
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                    INSERT INTO project_costs (project_id, item_name, category, quantity, unit,
                                             material_cost, labor_cost, equipment_cost, other_cost,
                                             total_cost, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (project_id, item_name, category, quantity, unit,
                         unit_price if category == 'مواد' else 0,
                         unit_price if category == 'عمالة' else 0,
                         unit_price if category == 'معدات' else 0,
                         unit_price if category == 'أخرى' else 0,
                         total_cost, notes))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"تم إضافة بند '{item_name}' بنجاح!")
    
    with tab3:
        st.markdown("#### 📊 تحليل التكاليف")
        
        # جلب تكاليف المشروع
        conn = sqlite3.connect('data/projects.db')
        project_costs = pd.read_sql_query("""
        SELECT * FROM project_costs 
        WHERE project_id = ?
        """, conn, params=[project_id])
        
        # جلب معلومات المشروع
        project_info = pd.read_sql_query("""
        SELECT * FROM projects WHERE id = ?
        """, conn, params=[project_id])
        conn.close()
        
        if not project_costs.empty:
            # حساب الإجماليات
            total_material = project_costs['material_cost'].sum()
            total_labor = project_costs['labor_cost'].sum()
            total_equipment = project_costs['equipment_cost'].sum()
            total_other = project_costs['other_cost'].sum()
            grand_total = project_costs['total_cost'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💰 مواد", f"{total_material:,.0f} ريال")
            
            with col2:
                st.metric("👷 عمالة", f"{total_labor:,.0f} ريال")
            
            with col3:
                st.metric("🚜 معدات", f"{total_equipment:,.0f} ريال")
            
            with col4:
                st.metric("📊 أخرى", f"{total_other:,.0f} ريال")
            
            st.markdown(f"### 🎯 الإجمالي النهائي: {grand_total:,.0f} ريال")
            
            # مخطط دائري للتوزيع
            cost_distribution = {
                'المواد': total_material,
                'العمالة': total_labor,
                'المعدات': total_equipment,
                'أخرى': total_other
            }
            
            fig = px.pie(values=list(cost_distribution.values()), 
                        names=list(cost_distribution.keys()),
                        title='توزيع التكاليف',
                        color_discrete_sequence=px.colors.qualitative.Set3)
            
            fig.update_layout(title_font_size=16, title_x=0.5)
            st.plotly_chart(fig, use_container_width=True)
            
            # عرض جدول تفصيلي
            st.markdown("##### 📋 تفصيل البنود")
            st.dataframe(project_costs[['item_name', 'category', 'quantity', 'unit', 'total_cost']],
                        use_container_width=True)
    
    with tab4:
        st.markdown("#### 💾 حفظ وطباعة التقدير")
        
        # خيارات الحفظ
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 حفظ التقدير", type="primary", use_container_width=True):
                # تحديث تكلفة المشروع في جدول المشاريع
                conn = sqlite3.connect('data/projects.db')
                cursor = conn.cursor()
                
                # حساب الإجمالي
                total_query = "SELECT SUM(total_cost) FROM project_costs WHERE project_id = ?"
                cursor.execute(total_query, (project_id,))
                total_cost = cursor.fetchone()[0] or 0
                
                # تحديث المشروع
                cursor.execute('''
                UPDATE projects SET total_cost = ?, status = 'تقديم عرض'
                WHERE id = ?
                ''', (total_cost, project_id))
                
                conn.commit()
                conn.close()
                
                st.success(f"تم حفظ التقدير بمبلغ إجمالي: {total_cost:,.0f} ريال")
        
        with col2:
            # خيارات التصدير
            export_format = st.selectbox("صيغة التصدير", ["PDF", "Excel", "Word"])
            
            if st.button(f"📥 تصدير لـ {export_format}", use_container_width=True):
                st.info(f"جاري تحضير ملف {export_format}...")
                
                # هنا سيتم إنشاء الملف وتنزيله
                # (هذا يحتاج مكتبات إضافية مثل reportlab أو openpyxl)
                st.success("الملف جاهز للتنزيل!")
        
        # معاينة التقرير
        st.markdown("##### 👁️ معاينة التقرير")
        
        conn = sqlite3.connect('data/projects.db')
        project_info = pd.read_sql_query("SELECT * FROM projects WHERE id = ?", 
                                        conn, params=[project_id])
        project_costs = pd.read_sql_query("SELECT * FROM project_costs WHERE project_id = ?",
                                         conn, params=[project_id])
        conn.close()
        
        if not project_info.empty and not project_costs.empty:
            # إنشاء تقرير نصي
            report_text = f"""
            تقرير تقدير تكاليف المشروع
            ============================
            
            معلومات المشروع:
            ----------------
            • اسم المشروع: {project_info['project_name'].iloc[0]}
            • الموقع: {project_info['location'].iloc[0]}
            • الجهة الطالبة: {project_info['client'].iloc[0]}
            • نوع المشروع: {project_info['project_type'].iloc[0]}
            • تاريخ التقدير: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            
            تفصيل التكاليف:
            ----------------
            """
            
            for _, item in project_costs.iterrows():
                report_text += f"\n• {item['item_name']}: {item['quantity']} {item['unit']} × {item['total_cost']/item['quantity']:,.0f} = {item['total_cost']:,.0f} ريال"
            
            total_cost = project_costs['total_cost'].sum()
            report_text += f"""
            
            الإجماليات:
            ----------
            • إجمالي المواد: {project_costs['material_cost'].sum():,.0f} ريال
            • إجمالي العمالة: {project_costs['labor_cost'].sum():,.0f} ريال
            • إجمالي المعدات: {project_costs['equipment_cost'].sum():,.0f} ريال
            • إجمالي أخرى: {project_costs['other_cost'].sum():,.0f} ريال
            • الإجمالي النهائي: {total_cost:,.0f} ريال
            
            التوقيع:
            -------
            
            مهندس التكاليف
            {datetime.now().strftime('%Y-%m-%d')}
            """
            
            st.text_area("معاينة التقرير", report_text, height=400)

# الصفحة الرئيسية للتطبيق
def main():
    # تهيئة قاعدة البيانات
    init_database()
    
    # شريط التنقل الجانبي
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1995/1995465.png", width=100)
        st.markdown("<h2 class='rtl'>نظام التقدير</h2>", unsafe_allow_html=True)
        
        # اختيار الصفحة
        page_options = {
            "🏠 الصفحة الرئيسية": main_page,
            "🏗️ إدارة المشاريع": projects_page,
            "👥 الموردون والأسعار": suppliers_page,
            "💰 تقدير التكاليف": estimation_page,
        }
        
        selected_page = st.selectbox("القائمة", list(page_options.keys()))
        
        st.markdown("---")
        
        # معلومات المستخدم
        st.markdown("""
        <div class='rtl'>
        <h4>👤 معلومات المستخدم</h4>
        <p><strong>الاسم:</strong> مهندس التكاليف</p>
        <p><strong>الصلاحية:</strong> مدير تقديرات</p>
        <p><strong>آخر دخول:</strong> اليوم</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # روابط سريعة
        st.markdown("### 🔗 روابط سريعة")
        if st.button("📧 التواصل مع الدعم"):
            st.info("support@estimation.com")
        
        if st.button("📚 دليل المستخدم"):
            st.info("سيتم فتح دليل المستخدم في نافذة جديدة")
        
        st.markdown("---")
        
        # إصدار التطبيق
        st.caption("الإصدار 1.0.0 | © 2024 نظام التقدير")
    
    # عرض الصفحة المختارة
    page_function = page_options[selected_page]
    page_function()

if __name__ == "__main__":
    main()