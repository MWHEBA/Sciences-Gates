"""
Utility functions for the core app.
Includes image validation, processing, and optimization utilities.
"""
import os
from io import BytesIO
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.conf import settings


# Image validation constants
MAX_FILE_SIZE = getattr(settings, 'MAX_UPLOAD_SIZE', 5242880)  # 5MB default
MAX_IMAGE_WIDTH = getattr(settings, 'MAX_IMAGE_WIDTH', 1920)  # 1920px default
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'GIF', 'WEBP'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def validate_image_file_size(file_obj):
    """
    Validate that uploaded image file does not exceed maximum file size.
    
    Args:
        file_obj: Django UploadedFile object
        
    Raises:
        ValidationError: If file size exceeds MAX_FILE_SIZE
    """
    if file_obj.size > MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise ValidationError(
            f'حجم الملف كبير جداً. الحد الأقصى هو {max_size_mb:.1f} ميجابايت.',
            code='file_too_large'
        )


def validate_image_format(file_obj):
    """
    Validate that uploaded file is a supported image format.
    
    Args:
        file_obj: Django UploadedFile object
        
    Raises:
        ValidationError: If file format is not supported
    """
    # Check file extension
    file_name = file_obj.name.lower()
    file_ext = os.path.splitext(file_name)[1]
    
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            'صيغة الملف غير مدعومة. الصيغ المدعومة: JPG, PNG, GIF, WebP',
            code='invalid_format'
        )
    
    # Check actual image format using PIL
    try:
        img = Image.open(file_obj)
        img.verify()
        
        # Reset file pointer after verify
        file_obj.seek(0)
        
        # Check if format is in allowed list
        if img.format not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError(
                'صيغة الصورة غير مدعومة. الصيغ المدعومة: JPG, PNG, GIF, WebP',
                code='invalid_image_format'
            )
    except Exception as e:
        raise ValidationError(
            'الملف المرفوع ليس صورة صحيحة أو قد يكون تالفاً.',
            code='invalid_image'
        )


def validate_image_dimensions(file_obj):
    """
    Validate that image dimensions are reasonable.
    
    Args:
        file_obj: Django UploadedFile object
        
    Raises:
        ValidationError: If image dimensions are invalid
    """
    try:
        img = Image.open(file_obj)
        width, height = img.size
        
        # Check minimum dimensions (at least 100x100)
        if width < 100 or height < 100:
            raise ValidationError(
                'الصورة صغيرة جداً. الحد الأدنى للأبعاد: 100x100 بكسل.',
                code='image_too_small'
            )
        
        # Reset file pointer
        file_obj.seek(0)
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(
            'خطأ في قراءة أبعاد الصورة.',
            code='dimension_error'
        )


def validate_image_upload(file_obj):
    """
    Comprehensive image validation combining all checks.
    
    Args:
        file_obj: Django UploadedFile object
        
    Raises:
        ValidationError: If any validation check fails
    """
    validate_image_file_size(file_obj)
    validate_image_format(file_obj)
    validate_image_dimensions(file_obj)


def resize_image_on_upload(image_file, max_width=None):
    """
    Resize image if it exceeds maximum width.
    Maintains aspect ratio and converts to RGB if necessary.
    
    Args:
        image_file: Django UploadedFile object
        max_width: Maximum width in pixels (uses MAX_IMAGE_WIDTH if not specified)
        
    Returns:
        ContentFile: Resized image file or original if no resize needed
    """
    if max_width is None:
        max_width = MAX_IMAGE_WIDTH
    
    try:
        img = Image.open(image_file)
        
        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Check if resize is needed
        width, height = img.size
        if width > max_width:
            # Calculate new height maintaining aspect ratio
            ratio = max_width / width
            new_height = int(height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Save resized image to BytesIO
        output = BytesIO()
        
        # Determine format from original file
        file_name = image_file.name.lower()
        if file_name.endswith('.png'):
            img.save(output, format='PNG', optimize=True)
            content_type = 'image/png'
        elif file_name.endswith('.gif'):
            img.save(output, format='GIF', optimize=True)
            content_type = 'image/gif'
        else:
            # Default to JPEG for JPG and WebP
            img.save(output, format='JPEG', quality=85, optimize=True)
            content_type = 'image/jpeg'
        
        output.seek(0)
        return ContentFile(output.getvalue(), name=image_file.name)
    
    except Exception as e:
        # If resize fails, return original file
        image_file.seek(0)
        return image_file


def compress_image(image_file, quality=85):
    """
    Compress image to reduce file size.
    
    Args:
        image_file: Django UploadedFile object
        quality: JPEG quality (1-100, default 85)
        
    Returns:
        ContentFile: Compressed image file
    """
    try:
        img = Image.open(image_file)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Save with compression
        output = BytesIO()
        file_name = image_file.name.lower()
        
        if file_name.endswith('.png'):
            img.save(output, format='PNG', optimize=True)
        elif file_name.endswith('.gif'):
            img.save(output, format='GIF', optimize=True)
        else:
            img.save(output, format='JPEG', quality=quality, optimize=True)
        
        output.seek(0)
        return ContentFile(output.getvalue(), name=image_file.name)
    
    except Exception as e:
        # If compression fails, return original
        image_file.seek(0)
        return image_file


def generate_webp_version(image_file):
    """
    Generate WebP version of an image for modern browsers.
    
    Args:
        image_file: Django UploadedFile object or file path
        
    Returns:
        tuple: (webp_content, webp_filename) or (None, None) if conversion fails
    """
    try:
        if isinstance(image_file, str):
            img = Image.open(image_file)
            base_name = os.path.splitext(os.path.basename(image_file))[0]
        else:
            img = Image.open(image_file)
            base_name = os.path.splitext(image_file.name)[0]
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Save as WebP
        output = BytesIO()
        img.save(output, format='WEBP', quality=85, method=6)
        output.seek(0)
        
        webp_filename = f'{base_name}.webp'
        return ContentFile(output.getvalue(), name=webp_filename), webp_filename
    
    except Exception as e:
        # WebP conversion not critical, return None
        return None, None


def get_image_dimensions(image_file):
    """
    Get dimensions of an image file.
    
    Args:
        image_file: Django UploadedFile object or file path
        
    Returns:
        tuple: (width, height) or (None, None) if unable to determine
    """
    try:
        if isinstance(image_file, str):
            img = Image.open(image_file)
        else:
            img = Image.open(image_file)
            image_file.seek(0)
        
        return img.size
    except Exception:
        return None, None


def process_image_with_webp(image_file, max_width=None, quality=85):
    """
    Advanced image processing: resize, compress, and generate WebP version.
    
    This function performs comprehensive image optimization:
    1. Resizes image if it exceeds max_width
    2. Compresses image to reduce file size
    3. Generates WebP version for modern browsers
    4. Maintains aspect ratio and converts color modes as needed
    
    Args:
        image_file: Django UploadedFile object
        max_width: Maximum width in pixels (uses MAX_IMAGE_WIDTH if not specified)
        quality: JPEG quality (1-100, default 85)
        
    Returns:
        dict: {
            'original': ContentFile with optimized original format,
            'webp': ContentFile with WebP version or None if conversion failed,
            'original_filename': str,
            'webp_filename': str or None,
            'dimensions': (width, height),
            'original_size': int (bytes),
            'webp_size': int or None (bytes)
        }
    """
    if max_width is None:
        max_width = MAX_IMAGE_WIDTH
    
    result = {
        'original': None,
        'webp': None,
        'original_filename': image_file.name,
        'webp_filename': None,
        'dimensions': None,
        'original_size': 0,
        'webp_size': None
    }
    
    try:
        img = Image.open(image_file)
        original_format = img.format
        
        # Store original dimensions
        result['dimensions'] = img.size
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if necessary
        width, height = img.size
        if width > max_width:
            ratio = max_width / width
            new_height = int(height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Save optimized original format
        output_original = BytesIO()
        file_name = image_file.name.lower()
        
        if file_name.endswith('.png'):
            img.save(output_original, format='PNG', optimize=True)
        elif file_name.endswith('.gif'):
            img.save(output_original, format='GIF', optimize=True)
        else:
            # Default to JPEG for JPG and WebP
            img.save(output_original, format='JPEG', quality=quality, optimize=True)
        
        output_original.seek(0)
        original_content = ContentFile(output_original.getvalue(), name=image_file.name)
        result['original'] = original_content
        result['original_size'] = len(output_original.getvalue())
        
        # Generate WebP version
        try:
            output_webp = BytesIO()
            img.save(output_webp, format='WEBP', quality=quality, method=6)
            output_webp.seek(0)
            
            webp_filename = os.path.splitext(image_file.name)[0] + '.webp'
            webp_content = ContentFile(output_webp.getvalue(), name=webp_filename)
            result['webp'] = webp_content
            result['webp_filename'] = webp_filename
            result['webp_size'] = len(output_webp.getvalue())
        except Exception as e:
            # WebP conversion is not critical, continue without it
            pass
        
        return result
    
    except Exception as e:
        # If processing fails, return original file
        image_file.seek(0)
        result['original'] = image_file
        result['original_size'] = image_file.size
        return result


def get_webp_image_url(image_url):
    """
    Get the WebP version URL for an image.
    
    Args:
        image_url: URL of the original image (e.g., '/media/universities/logos/logo.jpg')
        
    Returns:
        str: URL of the WebP version (e.g., '/media/universities/logos/logo.webp')
    """
    if not image_url:
        return None
    
    # Remove extension and add .webp
    base_url = os.path.splitext(image_url)[0]
    return f'{base_url}.webp'


def get_image_srcset(image_url, sizes=None):
    """
    Generate responsive image srcset for different screen sizes.
    
    Args:
        image_url: URL of the original image
        sizes: List of pixel densities (default: [1, 2] for 1x and 2x)
        
    Returns:
        str: srcset attribute value (e.g., 'image.jpg 1x, image@2x.jpg 2x')
    """
    if not image_url or not sizes:
        return None
    
    if sizes is None:
        sizes = [1, 2]
    
    srcset_parts = []
    base_url = os.path.splitext(image_url)[0]
    ext = os.path.splitext(image_url)[1]
    
    for size in sizes:
        if size == 1:
            srcset_parts.append(f'{image_url} 1x')
        else:
            sized_url = f'{base_url}@{size}x{ext}'
            srcset_parts.append(f'{sized_url} {size}x')
    
    return ', '.join(srcset_parts)


def optimize_image_for_web(image_file, max_width=None, quality=85, generate_webp=True):
    """
    Comprehensive image optimization for web serving.
    
    This is the main function to call for image optimization. It:
    1. Validates the image
    2. Resizes if necessary
    3. Compresses to reduce file size
    4. Optionally generates WebP version
    
    Args:
        image_file: Django UploadedFile object
        max_width: Maximum width in pixels (uses MAX_IMAGE_WIDTH if not specified)
        quality: JPEG quality (1-100, default 85)
        generate_webp: Whether to generate WebP version (default True)
        
    Returns:
        dict: {
            'success': bool,
            'original': ContentFile or None,
            'webp': ContentFile or None,
            'original_filename': str,
            'webp_filename': str or None,
            'dimensions': (width, height) or None,
            'original_size': int,
            'webp_size': int or None,
            'error': str or None
        }
    """
    result = {
        'success': False,
        'original': None,
        'webp': None,
        'original_filename': None,
        'webp_filename': None,
        'dimensions': None,
        'original_size': 0,
        'webp_size': None,
        'error': None
    }
    
    try:
        # Validate image first
        validate_image_upload(image_file)
        
        # Process image
        if generate_webp:
            process_result = process_image_with_webp(image_file, max_width, quality)
        else:
            # Just resize and compress without WebP
            original = resize_image_on_upload(image_file, max_width)
            original = compress_image(original, quality)
            process_result = {
                'original': original,
                'webp': None,
                'original_filename': image_file.name,
                'webp_filename': None,
                'dimensions': get_image_dimensions(original),
                'original_size': len(original.read()) if hasattr(original, 'read') else 0,
                'webp_size': None
            }
        
        result.update(process_result)
        result['success'] = True
        return result
    
    except ValidationError as e:
        result['error'] = str(e)
        return result
    except Exception as e:
        result['error'] = f'خطأ في معالجة الصورة: {str(e)}'
        return result


def clean_description(value):
    """
    Cleans up HTML description for card preview:
    1. Removes HTML comments.
    2. Unescapes HTML entities twice (to handle double escaping like &amp;nbsp;).
    3. Replaces non-breaking spaces (\xa0, &nbsp;) with standard spaces.
    4. Strips all HTML tags.
    5. Collapses multiple spaces into a single space.
    """
    import html
    import re
    from django.utils.html import strip_tags

    if not value:
        return ""
    
    # Remove HTML comments
    pattern = r'<!--.*?-->'
    value = re.sub(pattern, '', value, flags=re.DOTALL)
    
    # Unescape HTML entities (twice, just in case)
    value = html.unescape(html.unescape(value))
    
    # Replace non-breaking spaces with standard spaces
    value = value.replace('\xa0', ' ').replace('&nbsp;', ' ')
    value = value.replace('&amp;nbsp;', ' ')
    
    # Strip HTML tags
    value = strip_tags(value)
    
    # Collapse multiple whitespaces and strip leading/trailing whitespace
    value = re.sub(r'\s+', ' ', value).strip()
    
    return value

