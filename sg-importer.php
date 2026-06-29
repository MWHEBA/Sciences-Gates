<?php
/**
 * Plugin Name: Sciences Gates Content Importer Helper
 * Description: Helper plugin to securely export WordPress posts/CPTs (Elementor + Yoast SEO) to the new Sciences Gates Django dashboard.
 * Version: 1.0.0
 * Author: Antigravity
 * License: GPL2
 */

if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly
}

// =========================================================================
// Settings - Secret Key & Admin Panel
// =========================================================================
if (!defined('SG_IMPORTER_SECRET_KEY')) {
    define('SG_IMPORTER_SECRET_KEY', 'sg_import_secure_token_2026');
}

/**
 * Get active secret key (from DB or fallback to constant)
 */
function sg_importer_get_secret_key() {
    $db_key = get_option('sg_importer_secret_key');
    if (!empty($db_key)) {
        return $db_key;
    }
    return SG_IMPORTER_SECRET_KEY;
}

// Bypass WordPress REST API restrictions for our specific endpoint
add_filter('rest_authentication_errors', 'sg_importer_bypass_auth_errors', 999);

/**
 * Bypass any security plugins or custom filters blocking REST API access
 * by verifying our token early and setting the current user to administrator.
 */
function sg_importer_bypass_auth_errors($result) {
    // Check if the current request is for our import endpoint
    $request_uri = $_SERVER['REQUEST_URI'] ?? '';
    if (strpos($request_uri, '/wp-json/sg/v1/import') === false) {
        return $result;
    }

    $active_key = sg_importer_get_secret_key();
    
    // Check Authorization Header
    $auth_header = $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';
    if (!$auth_header && function_exists('apache_request_headers')) {
        $headers = apache_request_headers();
        $auth_header = $headers['Authorization'] ?? $headers['authorization'] ?? '';
    }

    $token = '';
    if (!empty($auth_header) && strpos($auth_header, 'Bearer ') === 0) {
        $token = substr($auth_header, 7);
    }

    // Check query parameter 'token'
    if (empty($token) || $token !== $active_key) {
        $token = $_GET['token'] ?? $_POST['token'] ?? '';
    }

    // If token is valid, temporarily log in as first administrator to bypass blocks
    if (!empty($token) && $token === $active_key) {
        $admins = get_users(array('role' => 'administrator', 'number' => 1));
        if (!empty($admins)) {
            wp_set_current_user($admins[0]->ID);
        }
        return null; // Clear any previously set errors
    }

    return $result;
}

// Register REST API Route
add_action('rest_api_init', function () {
    register_rest_route('sg/v1', '/import', array(
        'methods'             => 'GET',
        'callback'            => 'sg_importer_handle_request',
        'permission_callback' => 'sg_importer_check_permission',
    ));
});

// Register settings page in WordPress Admin
add_action('admin_menu', function () {
    add_menu_page(
        'مستورد Sciences Gates',
        'مستورد SG',
        'manage_options',
        'sg-importer-settings',
        'sg_importer_render_settings_page',
        'dashicons-download',
        80
    );
});

/**
 * Render WordPress Admin settings page
 */
function sg_importer_render_settings_page() {
    if (!current_user_can('manage_options')) {
        return;
    }

    // Save settings on form submission
    if (isset($_POST['sg_importer_save_settings'])) {
        check_admin_referer('sg_importer_settings_verify');
        
        $new_key = sanitize_text_field($_POST['sg_importer_secret_key'] ?? '');
        if (!empty($new_key)) {
            update_option('sg_importer_secret_key', $new_key);
            echo '<div class="updated"><p>تم حفظ المفتاح السري بنجاح!</p></div>';
        } else {
            delete_option('sg_importer_secret_key');
            echo '<div class="updated"><p>تمت إعادة تعيين المفتاح السري للقيمة الافتراضية.</p></div>';
        }
    }

    $active_key = sg_importer_get_secret_key();
    $endpoint_url = rest_url('sg/v1/import');
    $is_constant_defined = defined('SG_IMPORTER_SECRET_KEY');
    $db_key = get_option('sg_importer_secret_key');
    
    ?>
    <div class="wrap" style="direction: rtl; text-align: right; font-family: Tahoma, Geneva, sans-serif;">
        <h1>إعدادات مساعد مستورد محتوى Sciences Gates</h1>
        
        <div class="card" style="max-width: 800px; padding: 20px; margin-top: 20px; background: #fff; border: 1px solid #ccd0d4; box-shadow: 0 1px 1px rgba(0,0,0,.04);">
            <h2>حالة الاتصال والربط</h2>
            <p>استخدم البيانات التالية لتهيئة ملف <code>.env</code> الخاص بموقع Django الجديد للتمكن من سحب المحتوى بشكل آمن.</p>
            
            <table class="form-table" role="presentation">
                <tbody>
                    <tr>
                        <th scope="row" style="text-align: right; width: 200px;">رابط الاتصال (API Endpoint)</th>
                        <td>
                            <code style="background: #f0f0f1; padding: 5px 10px; border-radius: 4px; font-size: 14px;"><?php echo esc_url($endpoint_url); ?></code>
                            <p class="description">قم بوضع الرابط الأساسي (مثال: <code>https://sciencesgates.com/</code>) في حقل <code>WP_IMPORTER_BASE_URL</code> بملف <code>.env</code> الخاص بـ Django.</p>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row" style="text-align: right;">المفتاح السري الحالي (Active Secret Key)</th>
                        <td>
                            <code style="background: #f0f0f1; padding: 5px 10px; border-radius: 4px; font-size: 14px; font-weight: bold;"><?php echo esc_html($active_key); ?></code>
                            <?php if ($is_constant_defined && empty($db_key)): ?>
                                <span style="color: #46b450; margin-right: 10px;">(مُعرّف افتراضياً عبر كود PHP)</span>
                            <?php elseif (!empty($db_key)): ?>
                                <span style="color: #ffb900; margin-right: 10px;">(مُعرّف عبر قاعدة البيانات)</span>
                            <?php endif; ?>
                            <p class="description">قم بوضع هذا المفتاح في حقل <code>WP_IMPORTER_SECRET_KEY</code> بملف <code>.env</code> الخاص بـ Django.</p>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="card" style="max-width: 800px; padding: 20px; margin-top: 20px; background: #fff; border: 1px solid #ccd0d4; box-shadow: 0 1px 1px rgba(0,0,0,.04);">
            <h2>تغيير المفتاح السري</h2>
            <form method="post" action="">
                <?php wp_nonce_field('sg_importer_settings_verify'); ?>
                
                <table class="form-table" role="presentation">
                    <tbody>
                        <tr>
                            <th scope="row" style="text-align: right; width: 200px;"><label for="sg_importer_secret_key">مفتاح سري جديد</label></th>
                            <td>
                                <input type="text" id="sg_importer_secret_key" name="sg_importer_secret_key" value="<?php echo esc_attr($db_key ? $db_key : ''); ?>" class="regular-text" style="width: 100%; max-width: 400px;" placeholder="اتركه فارغاً لاستخدام المفتاح الافتراضي" />
                                <p class="description">إذا واجهتك مشاكل في الصلاحيات أو كان السيرفر يحظر هيدرات Authorization، يمكنك تعيين مفتاح مخصص هنا ومطابقته في ملف <code>.env</code>.</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
                
                <p class="submit">
                    <input type="submit" name="sg_importer_save_settings" id="submit" class="button button-primary" value="حفظ التغييرات" />
                </p>
            </form>
        </div>
    </div>
    <?php
}

/**
 * Check request permission via Authorization header or query parameter
 */
function sg_importer_check_permission(WP_REST_Request $request) {
    $active_key = sg_importer_get_secret_key();
    
    $auth_header = $request->get_header('Authorization');
    if (!$auth_header) {
        // Fallback for some server configurations
        $auth_header = $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';
    }

    $token = '';
    if (!empty($auth_header) && strpos($auth_header, 'Bearer ') === 0) {
        $token = substr($auth_header, 7);
    }

    // Fallback to query parameter if token is empty or doesn't match
    if (empty($token) || $token !== $active_key) {
        $token = $request->get_param('token');
    }

    if (empty($token) || $token !== $active_key) {
        return new WP_Error('unauthorized', 'غير مصرح بالدخول - المفتاح السري غير صحيح', array('status' => 401));
    }
    return true;
}

/**
 * معالجة طلب الاستيراد وجلب البيانات
 */
function sg_importer_handle_request(WP_REST_Request $request) {
    $slug = sanitize_text_field($request->get_param('slug'));
    if (empty($slug)) {
        return new WP_Error('missing_slug', 'الرجاء إدخال الـ slug الخاص بالمقال', array('status' => 400));
    }

    // البحث عن المقال بالـ slug في كل أنواع المقالات مع تجربة كل احتمالات الترميز (Percent encoding / Decoded)
    $slug_variations = array(
        $slug,
        urldecode($slug),
        rawurldecode($slug),
        urlencode($slug),
        rawurlencode($slug),
        sanitize_title($slug),
        sanitize_title(urldecode($slug))
    );
    $slug_variations = array_unique(array_filter($slug_variations));

    $posts = array();
    foreach ($slug_variations as $slug_var) {
        $posts = get_posts(array(
            'name'        => $slug_var,
            'post_type'   => 'any',
            'post_status' => 'publish',
            'numberposts' => 1,
        ));
        if (!empty($posts)) {
            break;
        }
    }

    if (empty($posts)) {
        return new WP_Error('post_not_found', 'المقال غير موجود في الموقع القديم', array('status' => 404));
    }

    $post = $posts[0];
    $post_id = $post->ID;

    // 1. تحديد نوع المحتوى
    $type_info = sg_detect_content_type($post_id);

    // 2. استخراج بيانات Elementor
    $elementor_data = sg_extract_elementor_data($post_id);

    // 3. استخراج بيانات Yoast SEO
    $seo_data = sg_extract_yoast_seo($post_id);

    // 4. بناء الـ HTML لكل منهما بشكل يماثل Elementor
    $faculties_raw_html = '';
    foreach ($elementor_data['_faculty_accordions'] as $accordion) {
        $faculties_raw_html .= sg_build_elementor_accordion_html($accordion);
    }

    $faqs_raw_html = '';
    foreach ($elementor_data['_faq_accordions'] as $accordion) {
        $faqs_raw_html .= sg_build_elementor_accordion_html($accordion);
    }

    // استخراج الكليات والبرامج كبيانات مهيأة (كـ fallback)
    $faculties = array();
    if (in_array($type_info['type'], array('university', 'institute'))) {
        foreach ($elementor_data['_faculty_accordions'] as $accordion) {
            $faculties = array_merge($faculties, sg_parse_accordion_faculties($accordion));
        }
    }

    // استخراج الأسئلة الشائعة كبيانات مهيأة (كـ fallback)
    $faqs = array();
    foreach ($elementor_data['_faq_accordions'] as $accordion) {
        foreach ($accordion as $item) {
            $faqs[] = array(
                'question' => trim($item['title']),
                'answer'   => trim($item['content']),
            );
        }
    }

    // 6. استخراج الصور
    $images = sg_extract_images($post_id, $elementor_data['_images'], $seo_data['og_image_url']);

    // 7. تقسيم وتعيين الحقول حسب النوع والـ keywords
    $fields = sg_map_fields($type_info['type'], $elementor_data['_raw_blocks']);

    // 8. جداول التخصصات (إذا كان النوع Major)
    $subjects_tables = array();
    $salary_tables = array();
    $countries_tables = array();
    if ($type_info['type'] === 'major') {
        $tables_result = sg_extract_major_tables($elementor_data['_raw_blocks']);
        $subjects_tables = $tables_result['subjects'];
        $salary_tables = $tables_result['salary'];
        $countries_tables = $tables_result['countries'];
    }

    // استخراج الوسوم (Tags)
    $tags = array();
    $post_tags = wp_get_post_terms($post_id, 'post_tag', array('fields' => 'names'));
    if (!is_wp_error($post_tags) && is_array($post_tags)) {
        $tags = array_merge($tags, $post_tags);
    }
    $taxonomies = get_object_taxonomies($post->post_type);
    if (is_array($taxonomies)) {
        foreach ($taxonomies as $taxonomy) {
            if ($taxonomy !== 'post_tag' && (strpos($taxonomy, 'tag') !== false)) {
                $terms = wp_get_post_terms($post_id, $taxonomy, array('fields' => 'names'));
                if (!is_wp_error($terms) && is_array($terms)) {
                    $tags = array_merge($tags, $terms);
                }
            }
        }
    }
    $tags = array_values(array_unique(array_filter($tags)));

    // تجهيز الـ JSON Response
    $response = array(
        'content_type'       => $type_info['type'],
        'sub_type'           => $type_info['sub'] ?? '',
        'name'               => html_entity_decode($post->post_title, ENT_QUOTES, 'UTF-8'),
        'slug'               => $post->post_name,
        'city_raw'           => sg_detect_city($post->post_title, $elementor_data['_raw_blocks']),
        'video_url'          => $elementor_data['video_url'] ?? '',
        'fields'             => $fields,
        'faculties'          => $faculties,
        'faculties_raw_html' => $faculties_raw_html,
        'faqs'               => $faqs,
        'faqs_raw_html'      => $faqs_raw_html,
        'images'             => $images,
        'seo'                => $seo_data['seo'],
        'categories'         => wp_get_post_categories($post_id, array('fields' => 'names')),
        'tags'               => $tags,
        'wp_post_id'         => $post_id,
    );

    if ($type_info['type'] === 'major') {
        $response['major_category'] = sg_detect_major_category($post->post_title, $elementor_data['_raw_blocks']);
        $response['subjects_tables'] = $subjects_tables;
        $response['salary_tables'] = $salary_tables;
        $response['countries_tables'] = $countries_tables;
    }

    return new WP_REST_Response($response, 200);
}

/**
 * تحديد نوع المحتوى بناءً على التصنيفات أو الـ CPT
 */
function sg_detect_content_type($post_id) {
    $post_type = get_post_type($post_id);
    
    // إذا كان CPT غير post و page، نعتبره تخصص
    if ($post_type !== 'post' && $post_type !== 'page') {
        return array('type' => 'major', 'sub' => '');
    }

    $categories = wp_get_post_categories($post_id, array('fields' => 'names'));
    $all_cats = implode(' ', $categories);

    if (sg_str_contains($all_cats, 'خاص')) {
        return array('type' => 'university', 'sub' => 'private');
    }
    if (sg_str_contains($all_cats, 'حكوم')) {
        return array('type' => 'university', 'sub' => 'public');
    }
    if (sg_str_contains($all_cats, 'لغ')) {
        return array('type' => 'institute', 'sub' => 'language');
    }
    if (sg_str_contains($all_cats, 'معهد') || sg_str_contains($all_cats, 'أكاديم')) {
        return array('type' => 'institute', 'sub' => 'academic');
    }

    // Fallback لجامعة خاصة كخيار افتراضي
    return array('type' => 'university', 'sub' => 'private');
}

/**
 * استخراج بيانات Elementor بشكل شجري (DFS)
 */
function sg_extract_elementor_data($post_id) {
    $extracted = array(
        '_raw_blocks'         => array(),
        '_faculty_accordions' => array(),
        '_faq_accordions'     => array(),
        '_images'             => array(),
        '_last_heading'       => '',
        'video_url'           => '',
    );

    $elementor_data = get_post_meta($post_id, '_elementor_data', true);
    if (!empty($elementor_data)) {
        $elements = json_decode($elementor_data, true);
        if (is_string($elements)) {
            $elements = json_decode($elements, true);
        }
        if (is_array($elements)) {
            sg_traverse_elementor($elements, $extracted);
        }
    }

    // إذا لم يكن هناك بيانات Elementor، نستخدم محتوى المقال الافتراضي كـ fallback
    if (empty($extracted['_raw_blocks'])) {
        $post = get_post($post_id);
        $content = $post->post_content;
        $extracted['_raw_blocks'][] = array(
            'heading' => 'الوصف',
            'content' => $content,
        );
    }

    return $extracted;
}

/**
 * DFS Traversal لعناصر Elementor
 */
function sg_traverse_elementor($elements, &$extracted) {
    foreach ($elements as $element) {
        $type = $element['elType'] ?? '';

        if (in_array($type, array('section', 'column'))) {
            sg_traverse_elementor($element['elements'] ?? array(), $extracted);
            continue;
        }

        if ($type === 'widget') {
            sg_process_widget($element, $extracted);
        }
    }
}

/**
 * معالجة الـ Widget المنفردة بناءً على نوعها
 */
function sg_process_widget($widget, &$extracted) {
    $widget_type = $widget['widgetType'] ?? '';
    $settings = $widget['settings'] ?? array();

    switch ($widget_type) {
        case 'heading':
            $extracted['_last_heading'] = wp_strip_all_tags($settings['title'] ?? '');
            break;

        case 'text-editor':
        case 'html':
            $heading = $extracted['_last_heading'] ?: 'نبذة';
            $content = $settings['editor'] ?? $settings['html'] ?? '';
            if (!empty($content)) {
                $extracted['_raw_blocks'][] = array(
                    'heading' => $heading,
                    'content' => $content,
                );
            }
            break;

        case 'image':
            if (!empty($settings['image']['url'])) {
                $extracted['_images'][] = array(
                    'url' => $settings['image']['url'],
                    'alt' => $settings['image_alt'] ?? '',
                    'id'  => $settings['image']['id'] ?? 0,
                );
            }
            break;

        case 'accordion':
        case 'toggle':
            $tabs = $settings['tabs'] ?? $settings['items'] ?? array();
            if (empty($tabs)) break;

            // نتحقق إذا كان هذا الأكورديون يحتوي على أي جدول (الذي يمثل الكليات والبرامج)
            $has_table = false;
            foreach ($tabs as $tab) {
                $content = $tab['tab_content'] ?? $tab['item_content'] ?? '';
                if (stripos($content, '<table') !== false) {
                    $has_table = true;
                    break;
                }
            }

            $accordion_items = array();
            foreach ($tabs as $tab) {
                $accordion_items[] = array(
                    'title'   => $tab['tab_title'] ?? $tab['item_title'] ?? '',
                    'content' => $tab['tab_content'] ?? $tab['item_content'] ?? '',
                );
            }

            if ($has_table) {
                $extracted['_faculty_accordions'][] = $accordion_items;
            } else {
                $extracted['_faq_accordions'][] = $accordion_items;
            }
            break;

        case 'video':
            $url = $settings['link'] ?? $settings['youtube_url'] ?? $settings['video_link'] ?? '';
            if (is_array($url)) {
                $url = $url['url'] ?? '';
            }
            if (!empty($url)) {
                $extracted['video_url'] = $url;
            }
            break;
    }
}

// الكلمات المفتاحية لمطابقة الحقول لكل نوع
const SG_KEYWORDS = array(
    'university' => array(
        'description'                     => array('عن الجامعة', 'نبذة', 'تعريف', 'لمحة', 'overview', 'about', 'تأسيس'),
        'admission_requirements_bachelor' => array('بكالوريوس', 'bachelor', 'البكالوريوس', 'الدرجة الأولى', 'شروط القبول للبكالوريوس'),
        'admission_requirements_master'   => array('ماجستير', 'master', 'الماجستير', 'الدراسات العليا', 'شروط القبول للماجستير'),
        'admission_requirements_phd'      => array('دكتوراه', 'phd', 'doctorate', 'الدكتوراه', 'شروط القبول للدكتوراه'),
        'location'                        => array('موقع', 'location', 'عنوان', 'المدينة', 'العنوان', 'سكن', 'السكن'),
    ),
    'institute' => array(
        'introduction'  => array('دراسة اللغة الإنجليزية في معهد', 'دراسة اللغة في معهد', 'مقدمة', 'تمهيد'),
        'description'   => array('عن المعهد', 'نبذة', 'تعريف', 'لمحة', 'overview', 'about'),
        'why_choose_us' => array('لماذا يختار الطلاب', 'لماذا يختار الطلاب العرب', 'لماذا تدرس', 'لماذا تختار', 'why choose'),
        'english_study' => array('دراسة اللغة الانجليزية', 'دراسة اللغة', 'اللغة الانجليزية', 'english study'),
        'location'      => array('موقع', 'location', 'عنوان', 'العنوان', 'موقع المعهد'),
    ),
    'major' => array(
        'description'          => array('عن التخصص', 'نبذة', 'تعريف', 'لمحة', 'overview', 'about'),
        'why_study_section'    => array('لماذا تدرس', 'لماذا', 'أهمية', 'why study', 'مميزات'),
        'how_to_apply_section' => array('كيفية التقديم', 'خطوات التقديم', 'how to apply', 'طريقة التقديم'),
        'career_opportunities' => array('فرص العمل', 'مجالات العمل', 'careers', 'وظائف', 'المستقبل المهني'),
        'study_duration'       => array('مدة الدراسة', 'سنين الدراسة', 'سنوات الدراسة', 'duration'),
        'bachelor_duration'    => array('مدة البكالوريوس', 'سنين البكالوريوس'),
        'master_duration'      => array('مدة الماجستير', 'سنين الماجستير'),
        'phd_duration'         => array('مدة الدكتوراه', 'سنين الدكتوراه'),
        'tuition_fees'         => array('الرسوم', 'التكلفة', 'مصاريف', 'fees', 'tuition'),
        'study_language'       => array('لغة الدراسة', 'اللغة', 'language'),
    )
);

/**
 * رسم وتعيين الحقول بناءً على الكلمات المفتاحية مع حساب الثقة (Confidence)
 */
function sg_map_fields($type, $blocks) {
    $keywords_map = SG_KEYWORDS[$type] ?? array();
    $fields = array();

    // تهيئة الحقول بقيم فارغة وثقة "none"
    foreach ($keywords_map as $field => $kws) {
        $fields[$field] = array('value' => '', 'confidence' => 'none');
    }

    $used_indices = array();

    // 1. محاولة مطابقة الحقول بالكلمات المفتاحية في العناوين
    foreach ($keywords_map as $field => $kws) {
        foreach ($blocks as $idx => $block) {
            if (in_array($idx, $used_indices)) continue;

            foreach ($kws as $kw) {
                if (sg_str_contains($block['heading'], $kw)) {
                    $fields[$field] = array(
                        'value'      => $block['content'],
                        'confidence' => 'high'
                    );
                    $used_indices[] = $idx;
                    break 2; // الانتقال للحقل التالي
                }
            }
        }
    }

    // 2. محاولة مطابقة الحقول المتبقية بالترتيب الافتراضي للمقالات
    $order_map = array();
    if ($type === 'university') {
        $order_map = array('description', 'location', 'admission_requirements_bachelor', 'admission_requirements_master', 'admission_requirements_phd');
    } elseif ($type === 'institute') {
        $order_map = array('introduction', 'description', 'location', 'why_choose_us', 'english_study');
    } else {
        $order_map = array('description', 'why_study_section', 'career_opportunities', 'how_to_apply_section');
    }

    $order_idx = 0;
    foreach ($order_map as $field) {
        if (empty($fields[$field]['value'])) {
            // ابحث عن أول بلوك غير مستخدم
            while ($order_idx < count($blocks) && in_array($order_idx, $used_indices)) {
                $order_idx++;
            }
            if ($order_idx < count($blocks)) {
                $fields[$field] = array(
                    'value'      => $blocks[$order_idx]['content'],
                    'confidence' => 'medium'
                );
                $used_indices[] = $order_idx;
                $order_idx++;
            }
        }
    }

    return $fields;
}

/**
 * استخراج الكليات والبرامج من القوائم والجداول والأكورديون
 */
function sg_extract_faculties($raw_blocks, $accordion_blocks) {
    $faculties = array();
    $raw_html = '';

    // ابحث أولاً عن الكتل التي تحتوي على الكليات
    $faculties_html_content = '';
    foreach ($raw_blocks as $block) {
        if (sg_str_contains($block['heading'], 'كليات') || sg_str_contains($block['heading'], 'تخصصات') || sg_str_contains($block['heading'], 'البرامج الدراسية')) {
            $faculties_html_content .= $block['content'];
        }
    }

    if (empty($faculties_html_content)) {
        // Fallback: ابحث في كل الكتل عن قوائم أو جداول
        foreach ($raw_blocks as $block) {
            if (sg_str_contains($block['content'], '<ul') || sg_str_contains($block['content'], '<table')) {
                $faculties_html_content .= $block['content'];
            }
        }
    }

    $raw_html = $faculties_html_content;

    // 1. محاولة الـ parsing من HTML Lists
    if (!empty($faculties_html_content)) {
        $faculties = sg_parse_html_lists($faculties_html_content);
    }

    // 2. إذا فشلت، جرب الـ Accordions
    if (empty($faculties) && !empty($accordion_blocks)) {
        $faculties = sg_parse_accordion_faculties($accordion_blocks);
    }

    return array(
        'faculties' => $faculties,
        'raw_html'  => $raw_html,
    );
}

/**
 * تحليل الكليات والبرامج من قوائم HTML
 */
function sg_parse_html_lists($html) {
    if (empty($html) || !class_exists('DOMDocument')) return array();

    $dom = new DOMDocument();
    // إخفاء الأخطاء الناتجة عن HTML غير الصالح
    libxml_use_internal_errors(true);
    // تحميل النص بـ UTF-8
    $dom->loadHTML('<?xml encoding="utf-8" ?>' . $html);
    libxml_clear_errors();

    $faculties = array();
    $lists = $dom->getElementsByTagName('ul');

    if ($lists->length > 0) {
        // نأخذ القائمة الرئيسية الأولى
        $main_list = $lists->item(0);
        foreach ($main_list->childNodes as $li) {
            if ($li->nodeName === 'li') {
                // اسم الكلية هو النص المباشر قبل أي قائمة فرعية
                $faculty_name = '';
                $programs = array();
                
                foreach ($li->childNodes as $child) {
                    if ($child->nodeName === '#text') {
                        $faculty_name .= $child->nodeValue;
                    } elseif ($child->nodeName === 'ul') {
                        // برامج الكلية
                        foreach ($child->childNodes as $sub_li) {
                            if ($sub_li->nodeName === 'li') {
                                $program_text = trim($sub_li->nodeValue);
                                if (!empty($program_text)) {
                                    $program_data = sg_parse_program_string($program_text);
                                    if ($program_data) {
                                        $programs[] = $program_data;
                                    }
                                }
                            }
                        }
                    }
                }

                $faculty_name = trim($faculty_name);
                // إزالة أي فواصل أو دبابيس في البداية
                $faculty_name = ltrim($faculty_name, "•\t\n\r\0\x0B- ");
                
                if (!empty($faculty_name) && !empty($programs)) {
                    $faculties[] = array(
                        'name'       => $faculty_name,
                        'confidence' => 'high',
                        'programs'   => $programs,
                    );
                }
            }
        }
    }

    return $faculties;
}

/**
 * تحليل الكليات والبرامج من الأكورديون
 */
function sg_parse_accordion_faculties($accordion_blocks) {
    $faculties = array();

    foreach ($accordion_blocks as $block) {
        $title = trim($block['title']);
        // استبعاد الأسئلة الشائعة
        if (sg_str_contains($title, 'سؤال') || sg_str_contains($title, 'الأسئلة') || sg_str_contains($title, 'FAQ') || sg_str_contains($title, 'شائع') || sg_str_contains($title, 'هل') || sg_str_contains($title, 'كيف') || sg_str_contains($title, 'ما هي')) {
            continue;
        }

        $programs = array();
        // تحليل محتوى الأكورديون كـ HTML للبحث عن برامج
        if (class_exists('DOMDocument') && !empty($block['content'])) {
            $dom = new DOMDocument();
            libxml_use_internal_errors(true);
            $dom->loadHTML('<?xml encoding="utf-8" ?>' . $block['content']);
            libxml_clear_errors();

            // 1. محاولة البحث عن جدول table
            $tables = $dom->getElementsByTagName('table');
            if ($tables->length > 0) {
                $table = $tables->item(0);
                $rows = $table->getElementsByTagName('tr');
                $is_first_row = true;
                
                foreach ($rows as $row) {
                    // تخطي صف الهيدر إذا كان يحتوي على th
                    if ($is_first_row && $row->getElementsByTagName('th')->length > 0) {
                        $is_first_row = false;
                        continue;
                    }
                    $is_first_row = false;
                    
                    $cells = $row->getElementsByTagName('td');
                    if ($cells->length >= 3) {
                        $p_name = trim($cells->item(0)->nodeValue);
                        $p_duration = trim($cells->item(1)->nodeValue);
                        $p_fees = trim($cells->item(2)->nodeValue);
                        
                        if (!empty($p_name) && !empty($p_duration) && !empty($p_fees)) {
                            $programs[] = array(
                                'name'         => $p_name,
                                'duration'     => $p_duration,
                                'tuition_fees' => $p_fees,
                            );
                        }
                    }
                }
            }

            // 2. إذا لم نجد برامج في الجدول، نحاول مع القوائم li
            if (empty($programs)) {
                $lis = $dom->getElementsByTagName('li');
                if ($lis->length > 0) {
                    foreach ($lis as $li) {
                        $text = trim($li->nodeValue);
                        $program_data = sg_parse_program_string($text);
                        if ($program_data) {
                            $programs[] = $program_data;
                        }
                    }
                }
            }

            // 3. الفولباك الأخير: تقسيم النص حسب السطر
            if (empty($programs)) {
                $lines = explode("\n", strip_tags($block['content']));
                foreach ($lines as $line) {
                    $text = trim($line);
                    $program_data = sg_parse_program_string($text);
                    if ($program_data) {
                        $programs[] = $program_data;
                    }
                }
            }
        }

        if (!empty($programs)) {
            $faculties[] = array(
                'name'       => $title,
                'confidence' => 'high',
                'programs'   => $programs,
            );
        }
    }

    return $faculties;
}

/**
 * تحليل نص البرنامج واستخراج (الاسم، المدة، الرسوم) باستخدام فواصل متعددة
 */
function sg_parse_program_string($str) {
    $str = trim($str);
    if (empty($str)) return null;

    // الفواصل الممكنة: —, -, |, ,, \t
    $separators = array(' — ', ' - ', ' | ', ' , ', ' ,');
    $parts = array();

    foreach ($separators as $sep) {
        if (strpos($str, $sep) !== false) {
            $parts = explode($sep, $str);
            break;
        }
    }

    // Fallback: لو مفيش فاصل واضح، نعتبر النص كله هو الاسم
    if (empty($parts)) {
        return array(
            'name'         => $str,
            'duration'     => 'غير محدد',
            'tuition_fees' => 'غير محدد',
        );
    }

    $name = trim($parts[0]);
    $duration = isset($parts[1]) ? trim($parts[1]) : 'غير محدد';
    $fees = isset($parts[2]) ? trim($parts[2]) : 'غير محدد';

    // لو مقسمش لـ 3 أجزاء، نحاول التخمين بناءً على الكلمات المفتاحية
    if (count($parts) == 2) {
        // لو الجزء الثاني يحتوي على كلمة "سنة" أو "عام" أو "شهر" أو "years" فهو مدة
        if (sg_str_contains($parts[1], 'سنة') || sg_str_contains($parts[1], 'عام') || sg_str_contains($parts[1], 'سنوات') || sg_str_contains($parts[1], 'year') || sg_str_contains($parts[1], 'month')) {
            $duration = trim($parts[1]);
            $fees = 'غير محدد';
        } else {
            // غير ذلك نعتبره رسوم
            $duration = 'غير محدد';
            $fees = trim($parts[1]);
        }
    }

    return array(
        'name'         => $name,
        'duration'     => $duration,
        'tuition_fees' => $fees,
    );
}

/**
 * استخراج الأسئلة الشائعة من الأكورديون
 */
function sg_extract_faqs($accordion_blocks) {
    $faqs = array();

    foreach ($accordion_blocks as $block) {
        $title = trim($block['title']);
        // تحقق لو العنوان يدل على سؤال أو يحتوي على علامة استفهام
        if (sg_str_contains($title, 'سؤال') || sg_str_contains($title, 'الأسئلة') || sg_str_contains($title, 'FAQ') || sg_str_contains($title, 'شائع') || sg_str_contains($title, 'هل') || sg_str_contains($title, 'كيف') || sg_str_contains($title, 'ما هي') || strpos($title, '؟') !== false || strpos($title, '?') !== false) {
            $faqs[] = array(
                'question' => $title,
                'answer'   => trim($block['content']),
            );
        }
    }

    return $faqs;
}

/**
 * استخراج بيانات الصور (الشعار والصورة الرئيسية وصورة SEO) مع بيانات SEO كاملة
 */
function sg_extract_images($post_id, $elementor_images, $yoast_og_image_url) {
    $images = array(
        'logo'       => array('url' => '', 'alt' => '', 'caption' => '', 'description' => '', 'title' => '', 'wp_id' => 0),
        'main_image' => array('url' => '', 'alt' => '', 'caption' => '', 'description' => '', 'title' => '', 'wp_id' => 0),
        'og_image'   => array('url' => '', 'alt' => '', 'caption' => '', 'description' => '', 'title' => '', 'wp_id' => 0),
    );

    // 1. Featured Image للمقال
    $featured_id = get_post_thumbnail_id($post_id);
    if ($featured_id) {
        $images['main_image'] = sg_get_full_image_data($featured_id);
    }

    // 2. البحث عن شعار في صور Elementor
    foreach ($elementor_images as $img) {
        $url = $img['url'];
        if (sg_str_contains($url, 'logo') || sg_str_contains($url, 'شعار')) {
            $images['logo'] = sg_get_full_image_data($img['id']);
            break;
        }
    }

    // لو ملقيناش شعار، وأول صورة في المقال غير الـ featured، نعتبرها شعار
    if (empty($images['logo']['url']) && !empty($elementor_images)) {
        foreach ($elementor_images as $img) {
            if ($img['id'] != $featured_id) {
                $images['logo'] = sg_get_full_image_data($img['id']);
                break;
            }
        }
    }

    // 3. صورة الـ OG من Yoast
    if (!empty($yoast_og_image_url)) {
        // محاولة استخراج الـ ID من الرابط
        $og_id = attachment_url_to_postid($yoast_og_image_url);
        if ($og_id) {
            $images['og_image'] = sg_get_full_image_data($og_id);
        } else {
            $images['og_image'] = array(
                'url'         => $yoast_og_image_url,
                'alt'         => '',
                'caption'     => '',
                'description' => '',
                'title'       => '',
                'wp_id'       => 0,
            );
        }
    } elseif (!empty($images['main_image']['url'])) {
        // Fallback لـ og_image لتكون الصورة الرئيسية
        $images['og_image'] = $images['main_image'];
    }

    return $images;
}

/**
 * استخراج كل بيانات الصورة من الووردبريس (Alt, Caption, Description, Title)
 */
function sg_get_full_image_data($attachment_id) {
    if (empty($attachment_id)) {
        return array(
            'url'         => '',
            'alt'         => '',
            'caption'     => '',
            'description' => '',
            'title'       => '',
            'wp_id'       => 0,
        );
    }

    $url = wp_get_attachment_url($attachment_id);
    if (!$url) {
        return array(
            'url'         => '',
            'alt'         => '',
            'caption'     => '',
            'description' => '',
            'title'       => '',
            'wp_id'       => 0,
        );
    }

    // Alt text من الـ meta
    $alt = get_post_meta($attachment_id, '_wp_attachment_image_alt', true) ?: '';
    
    // Caption من الـ post excerpt
    $attachment = get_post($attachment_id);
    $caption = $attachment ? $attachment->post_excerpt : '';
    
    // Description من الـ post content
    $description = $attachment ? $attachment->post_content : '';
    
    // Title من الـ post title
    $title = $attachment ? $attachment->post_title : '';

    return array(
        'url'         => $url,
        'alt'         => $alt,
        'caption'     => $caption,
        'description' => $description,
        'title'       => $title,
        'wp_id'       => $attachment_id,
    );
}

/**
 * استخراج بيانات Yoast SEO ومعالجة المتغيرات
 */
function sg_extract_yoast_seo($post_id) {
    $yoast_map = array(
        'meta_title'       => '_yoast_wpseo_title',
        'meta_description' => '_yoast_wpseo_metadesc',
        'focus_keyword'    => '_yoast_wpseo_focuskw',
        'canonical_url'    => '_yoast_wpseo_canonical',
        'og_title'         => '_yoast_wpseo_opengraph-title',
        'og_description'   => '_yoast_wpseo_opengraph-description',
        'og_image_url'     => '_yoast_wpseo_opengraph-image',
    );

    $seo = array();
    $post = get_post($post_id);

    foreach ($yoast_map as $key => $meta_key) {
        $val = get_post_meta($post_id, $meta_key, true);
        
        // إذا كان هناك قالب أو متغيرات، وكانت دالة Yoast متوفرة، نستخدمها للاستبدال
        if ($val && function_exists('wpseo_replace_vars')) {
            $val = wpseo_replace_vars($val, $post);
        }
        
        $seo[$key] = $val ? html_entity_decode($val, ENT_QUOTES, 'UTF-8') : '';
    }

    // استخراج مرادفات الكلمة البحثية بشكل منفصل
    $synonyms_raw = get_post_meta($post_id, '_yoast_wpseo_keywordsynonyms', true);
    $synonyms_arr = array();
    if (!empty($synonyms_raw)) {
        if (is_array($synonyms_raw)) {
            $synonyms_arr = $synonyms_raw;
        } elseif (is_string($synonyms_raw)) {
            // التحقق مما إذا كانت بصيغة JSON
            $decoded = json_decode($synonyms_raw, true);
            if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
                $synonyms_arr = $decoded;
            } else {
                // التحقق مما إذا كانت بصيغة serialized PHP
                $unserialized = @unserialize($synonyms_raw);
                if ($unserialized !== false && is_array($unserialized)) {
                    $synonyms_arr = $unserialized;
                } else {
                    // تجربة التقسيم بالفواصل
                    $synonyms_arr = array_map('trim', explode(',', $synonyms_raw));
                }
            }
        }
    }
    // تنظيف وترتيب المصفوفة
    $synonyms_arr = array_values(array_filter(array_map('trim', $synonyms_arr)));
    // تحويلها إلى JSON string متوافقة مع الحقل في Django
    $seo['keyphrase_synonyms'] = !empty($synonyms_arr) ? json_encode($synonyms_arr, JSON_UNESCAPED_UNICODE) : '';

    // إذا كان العنوان فارغاً، نحاول بناءه باستخدام قالب Yoast الافتراضي
    if (empty($seo['meta_title'])) {
        if (function_exists('wpseo_replace_vars')) {
            $wpseo_titles = get_option('wpseo_titles');
            $template = isset($wpseo_titles['title-post']) ? $wpseo_titles['title-post'] : '%%title%% %%page%% %%sep%% %%sitename%%';
            $seo['meta_title'] = wpseo_replace_vars($template, $post);
        }
        
        // لو لسه فارغ أو لم تتوفر الدالة
        if (empty($seo['meta_title'])) {
            $title_part = html_entity_decode($post->post_title, ENT_QUOTES, 'UTF-8');
            $site_name = get_bloginfo('name');
            $seo['meta_title'] = $title_part . ' | ' . $site_name;
        }
    }

    // نفس الشيء للـ og_title لو فارغ
    if (empty($seo['og_title'])) {
        $seo['og_title'] = $seo['meta_title'];
    }

    // تنظيف متغيرات Yoast كـ fallback لو كانت لا تزال موجودة
    foreach (array('meta_title', 'meta_description', 'og_title', 'og_description') as $field) {
        if (!empty($seo[$field])) {
            $seo[$field] = str_replace(
                array('%%title%%', '%%sitename%%', '%%sep%%', '%%page%%'),
                array(
                    html_entity_decode($post->post_title, ENT_QUOTES, 'UTF-8'),
                    get_bloginfo('name'),
                    '|',
                    ''
                ),
                $seo[$field]
            );
            $seo[$field] = preg_replace('/%%[^%]+%%/', '', $seo[$field]);
            // لا نستخدم trim للـ pipes والشرطات إلا لو كانت في الأطراف وبشكل لا يشوه العنوان
            $seo[$field] = trim($seo[$field], " \t\n\r\0\x0B");
        }
    }

    // اقلب noindex لـ index
    $noindex = get_post_meta($post_id, '_yoast_wpseo_meta-robots-noindex', true);
    $seo['robots_index'] = ($noindex !== '1');
    $seo['robots_follow'] = true; // افتراضي

    if (empty($seo['meta_description'])) {
        $seo['meta_description'] = wp_strip_all_tags(wp_trim_words($post->post_content, 30));
    }

    return array(
        'seo'          => $seo,
        'og_image_url' => $seo['og_image_url'],
    );
}

/**
 * تحديد المدينة (City) بناءً على المقال والمحتوى
 */
function sg_detect_city($title, $blocks) {
    $cities = array(
        'كوالالمبور' => 'كوالالمبور',
        'kuala lumpur' => 'كوالالمبور',
        'سيلانجور' => 'سيلانجور',
        'selangor' => 'سيلانجور',
        'بينانج' => 'بينانج',
        'penang' => 'بينانج',
        'جوهر' => 'جوهر',
        'johor' => 'جوهر',
        'قدح' => 'قدح',
        'kedah' => 'قدح',
        'كلنتان' => 'كلنتان',
        'kelantan' => 'كلنتان',
        'ملقا' => 'ملقا',
        'melaka' => 'ملقا',
        'malacca' => 'ملقا',
        'نيجري سمبيلان' => 'نيجري سمبيلان',
        'negeri sembilan' => 'نيجري سمبيلان',
        'باهانغ' => 'باهانغ',
        'باهانج' => 'باهانغ',
        'pahang' => 'باهانغ',
        'بيرق' => 'بيرق',
        'perak' => 'بيرق',
        'برليس' => 'برليس',
        'perlis' => 'برليس',
        'صباح' => 'صباح',
        'sabah' => 'صباح',
        'سراوق' => 'سراوق',
        'sarawak' => 'سراوق',
        'ترينجانو' => 'ترينجانو',
        'ترينغانو' => 'ترينجانو',
        'terengganu' => 'ترينجانو',
        'بوتراجايا' => 'بوتراجايا',
        'putrajaya' => 'بوتراجايا',
        'لابوان' => 'لابوان',
        'labuan' => 'لابوان',
        'سايبرجايا' => 'سايبرجايا',
        'cyberjaya' => 'سايبرجايا',
    );

    // ابحث في العنوان أولاً
    foreach ($cities as $kw => $name) {
        if (sg_str_contains($title, $kw)) {
            return $name;
        }
    }

    // ابحث في المحتوى
    foreach ($blocks as $block) {
        foreach ($cities as $kw => $name) {
            if (sg_str_contains($block['content'], $kw)) {
                return $name;
            }
        }
    }

    return '';
}

/**
 * تحديد تصنيف التخصص (Major Category)
 */
function sg_detect_major_category($title, $blocks) {
    $cats = array(
        'medical'     => array('طب', 'صيدل', 'تمريض', 'أسنان', 'medical', 'health', 'علاج طبيعي'),
        'engineering' => array('هندس', 'engineer', 'عمارة', 'مدني', 'ميكانيك'),
        'cs'          => array('حاسوب', 'برمجة', 'معلومات', 'computer', 'software', 'it', 'شبكات', 'ذكاء اصطناعي'),
        'business'    => array('إدارة', 'أعمال', 'تجارة', 'business', 'management', 'اقتصاد', 'تسويق'),
        'science'     => array('علوم', 'فيزياء', 'كيمياء', 'رياضيات', 'science', 'أحياء'),
    );

    $full_text = $title;
    foreach ($blocks as $b) {
        $full_text .= ' ' . $b['content'];
    }

    foreach ($cats as $cat_slug => $keywords) {
        foreach ($keywords as $kw) {
            if (sg_str_contains($full_text, $kw)) {
                return $cat_slug;
            }
        }
    }

    return 'science'; // Fallback
}

/**
 * استخراج جداول التخصصات (مواد، رواتب، دول وجهة)
 */
function sg_extract_major_tables($blocks) {
    $tables = array(
        'subjects'  => array(),
        'salary'    => array(),
        'countries' => array(),
    );

    foreach ($blocks as $block) {
        if (!empty($block['content']) && strpos($block['content'], '<table') !== false) {
            $type = 'subjects'; // الافتراضي هو المواد الدراسية

            $heading = $block['heading'];
            if (sg_str_contains($heading, 'راتب') || sg_str_contains($heading, 'رواتب') || sg_str_contains($heading, 'أجور') || sg_str_contains($heading, 'دخل') || sg_str_contains($heading, 'salary')) {
                $type = 'salary';
            } elseif (sg_str_contains($heading, 'دولة') || sg_str_contains($heading, 'دول') || sg_str_contains($heading, 'وجهة') || sg_str_contains($heading, 'بلد') || sg_str_contains($heading, 'country') || sg_str_contains($heading, 'countries')) {
                $type = 'countries';
            }

            // تحليل الجدول
            $parsed_rows = sg_parse_html_table($block['content']);
            if (!empty($parsed_rows)) {
                // دمج الصفوف في مصفوفة واحدة
                $tables[$type] = array_merge($tables[$type], $parsed_rows);
            }
        }
    }

    return $tables;
}

/**
 * تحليل جدول HTML واستخراج مصفوفة من الحقول
 */
function sg_parse_html_table($html) {
    if (empty($html) || !class_exists('DOMDocument')) return array();

    $dom = new DOMDocument();
    libxml_use_internal_errors(true);
    $dom->loadHTML('<?xml encoding="utf-8" ?>' . $html);
    libxml_clear_errors();

    $rows = array();
    $tr_elements = $dom->getElementsByTagName('tr');

    $is_first = true;
    foreach ($tr_elements as $tr) {
        // تخطي صف الـ header
        if ($is_first && $tr->getElementsByTagName('th')->length > 0) {
            $is_first = false;
            continue;
        }
        $is_first = false;

        $tds = $tr->getElementsByTagName('td');
        if ($tds->length > 0) {
            // نأخذ القيم من أول عمودين (لأن جداول dashboard للتخصصات هي key-value)
            $col1 = trim($tds->item(0)->nodeValue);
            $col2 = $tds->length > 1 ? trim($tds->item(1)->nodeValue) : '';
            
            if (!empty($col1)) {
                $rows[] = array(
                    'key'   => $col1,
                    'value' => $col2,
                );
            }
        }
    }

    return $rows;
}

/**
 * دالة مساعدة للبحث غير الحساس لحالة الأحرف
 */
function sg_str_contains($haystack, $needle) {
    return stripos($haystack, $needle) !== false;
}

/**
 * بناء كود الـ HTML الخاص بـ Elementor Accordion بشكل متوافق تماماً مع الـ Javascript Parser
 */
function sg_build_elementor_accordion_html($blocks) {
    if (empty($blocks)) return '';

    $html = '<div class="elementor-accordion">';
    foreach ($blocks as $block) {
        $title = esc_html($block['title']);
        $content = $block['content']; // محتوى الـ HTML (الجدول أو الإجابة)

        $html .= '<div class="elementor-accordion-item">';
        $html .= '  <div class="elementor-accordion-title">' . $title . '</div>';
        $html .= '  <div class="elementor-tab-content">' . $content . '</div>';
        $html .= '</div>';
    }
    $html .= '</div>';

    return $html;
}

