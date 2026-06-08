# WordPress Importer API Documentation

## نظرة عامة

دليل لـ WordPress plugin عشان يبعت البيانات بالشكل الصحيح للنظام الجديد.

---

## API Endpoint

```
GET /wp-json/sg/v1/import?slug={slug}&token={secret_key}
```

### Authentication

```http
Authorization: Bearer {secret_key}
```

---

## Response Format (JSON)

### حقول الصور الإلزامية والاختيارية

كل صورة لازم يكون ليها الحقول دي:

```json
{
  "url": "https://example.com/image.jpg",      // إلزامي
  "alt": "وصف دقيق للصورة للـ SEO",            // إلزامي - الأهم للـ SEO
  "caption": "نص يظهر للزوار تحت الصورة",      // اختياري - مفيد للـ SEO
  "description": "وصف داخلي لإدارة المكتبة"    // اختياري - للإدارة الداخلية
}
```

### أهمية كل حقل:

| الحقل | الأهمية | الاستخدام | ملاحظات |
|------|---------|-----------|---------|
| `url` | 10/10 | رابط الصورة | إلزامي |
| `alt` | 10/10 | النص البديل للـ SEO | إلزامي - الطول المثالي 80-140 حرف |
| `caption` | 6/10 | نص مرئي للزوار | اختياري لكن مُوصى به للـ SEO |
| `description` | 4/10 | وصف داخلي | اختياري - للإدارة الداخلية فقط |

---

## مثال كامل للـ Response

### University (جامعة)

```json
{
  "type": "university",
  "slug": "جامعة-مالايا",
  "fields": {
    "name": {"value": "جامعة مالايا", "confidence": "high"},
    "description": {"value": "وصف الجامعة...", "confidence": "high"},
    "location": {"value": "كوالالمبور، ماليزيا", "confidence": "high"}
  },
  "images": {
    "logo": {
      "url": "https://old-site.com/wp-content/uploads/logo-um.png",
      "alt": "شعار جامعة مالايا الماليزية UM",
      "caption": "",
      "description": "Logo file imported from WordPress"
    },
    "main_image": {
      "url": "https://old-site.com/wp-content/uploads/um-campus.jpg",
      "alt": "حرم جامعة مالايا الماليزية في كوالالمبور مع المباني الأكاديمية والمساحات الخضراء",
      "caption": "حرم جامعة مالايا - أعرق جامعة في ماليزيا",
      "description": "Main campus image showing academic buildings"
    },
    "og_image": {
      "url": "https://old-site.com/wp-content/uploads/um-og-image.jpg",
      "alt": "جامعة مالايا - الدراسة في ماليزيا",
      "caption": "",
      "description": "Social media sharing image"
    }
  },
  "seo": {
    "meta_title": "جامعة مالايا الماليزية UM | البرامج والتكاليف | يو إم 2026",
    "meta_description": "دليل شامل لجامعة مالايا...",
    "focus_keyword": "جامعة مالايا",
    "og_title": "الدراسة في جامعة مالايا الماليزية",
    "og_description": "اكتشف برامج جامعة مالايا..."
  }
}
```

### Institute (معهد)

```json
{
  "type": "institute",
  "slug": "معهد-els",
  "fields": {
    "name": {"value": "معهد ELS للغة الإنجليزية", "confidence": "high"},
    "description": {"value": "وصف المعهد...", "confidence": "high"}
  },
  "images": {
    "main_image": {
      "url": "https://old-site.com/wp-content/uploads/els-institute.jpg",
      "alt": "معهد ELS للغة الإنجليزية في كوالالمبور - فصول دراسية حديثة",
      "caption": "معهد ELS - تعلم اللغة الإنجليزية بكفاءة عالية",
      "description": "Institute building exterior"
    },
    "og_image": {
      "url": "https://old-site.com/wp-content/uploads/els-og.jpg",
      "alt": "معهد ELS - دورات اللغة الإنجليزية في ماليزيا",
      "caption": "",
      "description": "Social sharing image"
    }
  },
  "seo": {
    "meta_title": "معهد ELS للغة الإنجليزية في ماليزيا | الدورات والأسعار",
    "meta_description": "تعرف على دورات معهد ELS...",
    "focus_keyword": "معهد els"
  }
}
```

### Major (تخصص)

```json
{
  "type": "major",
  "slug": "هندسة-البرمجيات",
  "fields": {
    "name": {"value": "هندسة البرمجيات", "confidence": "high"},
    "description": {"value": "وصف التخصص...", "confidence": "high"}
  },
  "images": {
    "main_image": {
      "url": "https://old-site.com/wp-content/uploads/software-engineering.jpg",
      "alt": "طلاب هندسة البرمجيات يعملون على مشاريع برمجية في مختبر حديث بجامعة ماليزية",
      "caption": "هندسة البرمجيات - تخصص المستقبل في ماليزيا",
      "description": "Students working in software lab"
    },
    "og_image": {
      "url": "https://old-site.com/wp-content/uploads/software-og.jpg",
      "alt": "دراسة هندسة البرمجيات في ماليزيا",
      "caption": "",
      "description": "Social media image for software engineering major"
    }
  },
  "seo": {
    "meta_title": "هندسة البرمجيات في ماليزيا | الجامعات والتكاليف",
    "meta_description": "دليل شامل لدراسة هندسة البرمجيات...",
    "focus_keyword": "هندسة البرمجيات"
  }
}
```

---

## أفضل الممارسات لكتابة Alt Text

### ✅ افعل:

1. **اكتب وصف دقيق وواضح (80-140 حرف)**
   ```json
   "alt": "أخصائية تجميل تقوم بجلسة علاج الوجه في سبا سيرينيتي بالقاهرة"
   ```

2. **صف السياق مش بس الصورة**
   ```json
   "alt": "طلاب جامعة مالايا في مختبر الهندسة الكيميائية أثناء التجربة العملية"
   ```

3. **اذكر الموقع أو العلامة التجارية**
   ```json
   "alt": "حرم جامعة التكنولوجيا الماليزية في كوالالمبور مع برج الإدارة الرئيسي"
   ```

### ❌ لا تفعل:

1. **لا تحشو keywords**
   ```json
   // ❌ سيء
   "alt": "جامعة مالايا جامعة ماليزيا دراسة ماليزيا كوالالمبور تعليم جامعات"
   
   // ✅ جيد
   "alt": "حرم جامعة مالايا في كوالالمبور - أعرق جامعة في ماليزيا"
   ```

2. **لا تستخدم "صورة" أو "Image"**
   ```json
   // ❌ سيء
   "alt": "صورة لجامعة مالايا"
   
   // ✅ جيد
   "alt": "جامعة مالايا - المبنى الإداري الرئيسي في الحرم الجامعي"
   ```

3. **لا تترك Alt فارغ**
   ```json
   // ❌ سيء
   "alt": ""
   
   // ✅ جيد
   "alt": "شعار جامعة مالايا الماليزية"
   ```

---

## كيف تجهز البيانات في WordPress

### في WordPress Plugin

```php
<?php
// Example: Get image data with all SEO fields
function sg_get_image_data($attachment_id) {
    if (!$attachment_id) {
        return null;
    }
    
    $image_url = wp_get_attachment_url($attachment_id);
    
    return [
        'url' => $image_url,
        'alt' => get_post_meta($attachment_id, '_wp_attachment_image_alt', true) ?: '',
        'caption' => wp_get_attachment_caption($attachment_id) ?: '',
        'description' => get_post($attachment_id)->post_content ?: '',
    ];
}

// Example: Prepare logo data
$logo_id = get_post_meta($post_id, 'logo', true);
$response['images']['logo'] = sg_get_image_data($logo_id);

// Example: Prepare main image data
$main_image_id = get_post_thumbnail_id($post_id);
$response['images']['main_image'] = sg_get_image_data($main_image_id);

// Example: Prepare OG image
$og_image_id = get_post_meta($post_id, 'og_image', true);
$response['images']['og_image'] = sg_get_image_data($og_image_id);
?>
```

---

## Fallback Behavior (السلوك الاحتياطي)

إذا لم يتم تمرير بعض الحقول:

| الحقل المفقود | السلوك |
|---------------|---------|
| `url` | يتم تخطي الصورة بالكامل |
| `alt` | يتم توليد alt text تلقائياً من اسم الكيان (مثال: "شعار جامعة مالايا") |
| `caption` | يظل فارغاً (لا مشكلة) |
| `description` | يظل فارغاً (لا مشكلة) |

---

## Testing

لاختبار أن البيانات صحيحة:

1. تأكد أن JSON response يحتوي على الحقول المطلوبة
2. تأكد أن `alt` text موجود ووصفي (80-140 حرف مثالي)
3. إذا كان عندك `caption` في WordPress، أرسله
4. إذا كان عندك `description` في الـ media library، أرسله

---

## المزايا الجديدة (2026)

### Schema.org Markup
النظام الجديد بيضيف تلقائياً Schema.org ImageObject markup:

```html
<figure itemscope itemtype="https://schema.org/ImageObject">
    <img src="..." alt="..." itemprop="contentUrl">
    <figcaption itemprop="caption">...</figcaption>
</figure>
```

### WebP Optimization
كل الصور بتتحول تلقائياً لـ WebP عشان:
- تحميل أسرع
- استهلاك bandwidth أقل
- SEO أفضل (Core Web Vitals)

### SEO-Friendly File Names
أسماء الملفات بتبقى وصفية:
- قبل: `20240608_123456_abc123.jpg`
- بعد: `um-campus-main-building_20240608_123456_abc123.webp`

---

## Contact

لو في أي استفسار أو مشكلة في الـ import، تواصل مع الفريق التقني.
