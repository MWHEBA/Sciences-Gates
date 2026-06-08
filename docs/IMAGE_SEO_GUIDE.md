# دليل تحسين SEO للصور - 2026

## نظرة عامة

تم تحديث نظام إدارة الوسائط ليتوافق مع أفضل ممارسات SEO للصور في 2026، بناءً على توصيات Google وخبراء SEO.

## الحقول المتاحة في MediaFile

### 1. **Alt Text (النص البديل)** ⭐ الأهم
- **الأهمية:** 10/10
- **الاستخدام:** إلزامي لكل صورة
- **الطول المثالي:** 80-140 حرف
- **الغرض:** 
  - يستخدمه محركات البحث لفهم محتوى الصورة
  - يقرأه قارئ الشاشة للمستخدمين ضعاف البصر
  - يظهر عندما تفشل الصورة في التحميل

**مثال جيد:**
```
أخصائية تجميل تقوم بجلسة علاج الوجه في سبا سيرينيتي بالقاهرة
```

**مثال سيء:**
```
صورة
IMG_1234
```

### 2. **Caption (التسمية التوضيحية)**
- **الأهمية:** 6/10
- **الاستخدام:** اختياري لكن مُوصى به
- **الحد الأقصى:** 300 حرف
- **الغرض:**
  - نص مرئي يظهر للزوار أسفل الصورة
  - يضيف سياق إضافي للصورة
  - مفيد للـ SEO لأن Google يقرأ النص المحيط بالصورة

**مثال جيد:**
```
جلسة علاج الوجه المتقدم - احجزي الآن واحصلي على خصم 20%
```

### 3. **Title (عنوان الصورة)**
- **الأهمية:** 3/10
- **الاستخدام:** اختياري
- **الحد الأقصى:** 500 حرف
- **الغرض:**
  - يظهر عند التمرير على الصورة (tooltip)
  - Google تتجاهله في الـ indexing

### 4. **Description (الوصف الداخلي)**
- **الأهمية:** 4/10 (للإدارة الداخلية)
- **الاستخدام:** اختياري
- **الغرض:**
  - وصف تفصيلي للاستخدام الداخلي فقط
  - لا يظهر للزوار
  - مفيد لإدارة مكتبة كبيرة من الصور

---

## استخدام Template Tags الجديدة

### 1. **seo_image** - للصور المحسّنة للـ SEO

استخدم هذا الـ tag لعرض صور محسّنة مع Schema.org markup:

```django
{% load image_tags %}

{# مع caption #}
{% seo_image media.file.url media.alt_text media.caption media.width media.height "w-full rounded-lg" %}

{# بدون caption #}
{% seo_image university.main_image.url university.main_image_alt "" 800 600 "w-full" %}

{# مع eager loading للصور فوق الطية #}
{% seo_image hero_image.url "بوابات العلوم" "" 1200 630 "w-full" "eager" %}
```

**الناتج HTML:**
```html
<figure itemscope itemtype="https://schema.org/ImageObject" class="seo-image-figure">
    <picture>
        <source srcset="/media/image.webp" type="image/webp">
        <img src="/media/image.jpg" 
             alt="أخصائية تجميل تقوم بعلاج الوجه" 
             class="w-full rounded-lg" 
             loading="lazy"
             width="800" height="600"
             itemprop="contentUrl">
    </picture>
    <figcaption itemprop="caption" class="seo-image-caption">
        جلسة علاج الوجه المتقدم - احجزي الآن
    </figcaption>
</figure>
```

### 2. **media_file_image** - للاستخدام المباشر مع MediaFile

استخدم هذا الـ tag عندما يكون لديك instance من MediaFile:

```django
{% load image_tags %}

{# يستخدم تلقائياً كل حقول الـ SEO من MediaFile #}
{% media_file_image article.featured_image_obj "w-full rounded-lg" %}

{# مع eager loading #}
{% media_file_image university.logo_obj "h-20" "eager" %}
```

---

## تحسين تسمية الملفات

النظام الآن يقوم بإنشاء أسماء ملفات صديقة لـ SEO تلقائياً:

**قبل:**
```
20240608_123456_abc12345.jpg
```

**بعد:**
```
serenity-spa-treatment_20240608_123456_abc12345.jpg
```

هذا يحسن من:
- فهم محركات البحث لمحتوى الصورة
- ترتيب الصور في Google Images
- تجربة المستخدم عند تنزيل الصور

---

## أفضل الممارسات 2026

### ✅ افعل:

1. **اكتب alt text وصفياً ودقيقاً**
   - ركز على السياق مش بس الصورة
   - استخدم 80-140 حرف
   - اذكر الموقع/العلامة التجارية إذا كان مهماً

2. **استخدم caption للمعلومات الإضافية**
   - معلومات CTA (دعوة للإجراء)
   - الإسناد أو المصدر
   - سياق إضافي مفيد للزائر

3. **حدد أبعاد الصور دائماً**
   - يحسن Core Web Vitals (CLS)
   - يمنع Layout Shift

4. **استخدم lazy loading إلا للصور فوق الطية**
   - Lazy loading للصور تحت الطية
   - Eager loading للصور فوق الطية (hero images)

### ❌ لا تفعل:

1. **لا تحشو keywords في alt text**
   ```
   ❌ سبا سيرينيتي القاهرة علاج وجه تجميل عناية بالبشرة سبا ماساج
   ✅ أخصائية تجميل تقوم بعلاج الوجه في سبا سيرينيتي بالقاهرة
   ```

2. **لا تستخدم "صورة" أو "Image" في alt text**
   ```
   ❌ صورة لسبا سيرينيتي
   ✅ سبا سيرينيتي - غرفة علاج فخمة مع إضاءة طبيعية
   ```

3. **لا تترك alt text فارغاً**
   - كل صورة لازم يكون ليها alt text
   - استخدم الفلتر في Media Library لإيجاد الصور بدون alt

4. **لا تنسخ caption في alt text**
   - Alt text: وصف الصورة نفسها
   - Caption: معلومات إضافية للزائر

---

## استخدام Media Library

### البحث عن الصور بدون Alt Text:

1. افتح **Dashboard > مكتبة الوسائط**
2. فعّل checkbox **"صور بدون نص بديل (Alt)"**
3. اضغط **تصفية**
4. اللمبة الحمراء تشير للصور بدون alt text

### تحديث حقول SEO:

1. اضغط على أي صورة
2. املأ الحقول:
   - **Alt Text** (إلزامي) - 80-140 حرف مثالي
   - **Caption** (اختياري) - يظهر للزوار
   - **Title** (اختياري) - tooltip
   - **Description** (اختياري) - للإدارة الداخلية
3. اضغط **حفظ التعديلات**

### التحديث الجماعي:

1. اضغر **تحديد جماعي**
2. حدد الصور المطلوبة
3. يمكن الحذف الجماعي (لا يوجد تحديث جماعي للحقول حالياً)

---

## Schema.org Markup

النظام يضيف تلقائياً Schema.org ImageObject markup عند استخدام `seo_image` أو `media_file_image`:

```html
<figure itemscope itemtype="https://schema.org/ImageObject">
    <img itemprop="contentUrl" src="..." alt="...">
    <figcaption itemprop="caption">...</figcaption>
</figure>
```

هذا يساعد:
- محركات البحث على فهم الصور بشكل أفضل
- منصات AI (ChatGPT, Claude, Perplexity) على استخدام الصور
- Google Images على عرض معلومات أفضل

---

## Styling للـ Captions

الـ CSS موجود في `static/css/seo-image.css` ويشمل:

### الأنماط الأساسية:
```css
.seo-image-caption {
    font-size: 0.875rem;
    color: var(--text-muted);
    text-align: center;
    padding: 0.5rem 0.75rem;
    background-color: var(--surface-2);
}
```

### أنماط إضافية:
```django
{# مع border #}
<figure class="seo-image-figure bordered">

{# مركّز #}
<figure class="seo-image-figure centered">

{# caption صغير #}
<figure class="seo-image-figure compact">
```

---

## Migration Notes

تم إضافة الحقول الجديدة في `core/migrations/0005_*`:
- `caption` (TextField, max_length=300)
- `description` (TextField)
- تحديث help_text لـ `alt_text` و `title`

جميع الحقول الجديدة `blank=True` لذلك لا تحتاج تحديث البيانات القديمة إلزامياً، لكن يُنصح بإضافة alt text لجميع الصور.

---

## Resources

- [Google Images Best Practices](https://developers.google.com/search/docs/appearance/google-images)
- [Schema.org ImageObject](https://schema.org/ImageObject)
- [AltText.ai - SEO Best Practices 2026](https://alttext.ai/blog/image-alt-text-seo-best-practices)
- [Digital Applied - Image SEO Guide 2026](https://www.digitalapplied.com/blog/image-seo-complete-optimization-guide-2026)

---

## الأولويات للتطبيق

### أولوية عليا (الآن):
1. ✅ إضافة alt text لكل الصور في Media Library
2. ✅ استخدام `{% seo_image %}` في templates الجديدة
3. ✅ إضافة captions للصور المهمة (hero images, product images)

### أولوية متوسطة (لاحقاً):
1. ⏳ تحديث templates الموجودة لاستخدام SEO tags
2. ⏳ إضافة bulk update للـ alt text
3. ⏳ AI-powered alt text generation

### أولوية منخفضة:
1. ⏳ Image compression automation
2. ⏳ Auto WebP conversion
3. ⏳ CDN integration
