"""
Tests for advanced image optimization functionality.
Tests image compression, WebP generation, and responsive image serving.
"""
import os
import tempfile
from io import BytesIO
from PIL import Image
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from apps.core.utils import (
    validate_image_upload,
    validate_image_file_size,
    validate_image_format,
    validate_image_dimensions,
    resize_image_on_upload,
    compress_image,
    generate_webp_version,
    process_image_with_webp,
    optimize_image_for_web,
    get_webp_image_url,
    get_image_dimensions,
)


class ImageValidationTests(TestCase):
    """Test image validation utilities."""
    
    def setUp(self):
        """Create test images."""
        self.valid_image = self._create_test_image('test.jpg', 'JPEG', (800, 600))
        self.large_image = self._create_test_image('large.jpg', 'JPEG', (5000, 4000))
        self.small_image = self._create_test_image('small.jpg', 'JPEG', (50, 50))
    
    def _create_test_image(self, filename, format_type, size):
        """Helper to create test image."""
        img = Image.new('RGB', size, color='red')
        img_io = BytesIO()
        img.save(img_io, format=format_type)
        img_io.seek(0)
        return SimpleUploadedFile(filename, img_io.getvalue(), content_type='image/jpeg')
    
    def test_validate_image_file_size_valid(self):
        """Test file size validation with valid size."""
        # Should not raise
        validate_image_file_size(self.valid_image)
    
    def test_validate_image_file_size_too_large(self):
        """Test file size validation with oversized file."""
        # Create a file larger than 5MB
        large_file = SimpleUploadedFile(
            'large.jpg',
            b'x' * (5242880 + 1),
            content_type='image/jpeg'
        )
        with self.assertRaises(ValidationError):
            validate_image_file_size(large_file)
    
    def test_validate_image_format_valid(self):
        """Test format validation with valid format."""
        validate_image_format(self.valid_image)
    
    def test_validate_image_dimensions_valid(self):
        """Test dimension validation with valid dimensions."""
        validate_image_dimensions(self.valid_image)
    
    def test_validate_image_dimensions_too_small(self):
        """Test dimension validation with too small image."""
        with self.assertRaises(ValidationError):
            validate_image_dimensions(self.small_image)
    
    def test_validate_image_upload_comprehensive(self):
        """Test comprehensive image validation."""
        # Should not raise
        validate_image_upload(self.valid_image)


class ImageProcessingTests(TestCase):
    """Test image processing utilities."""
    
    def setUp(self):
        """Create test images."""
        self.test_image = self._create_test_image('test.jpg', 'JPEG', (2000, 1500))
    
    def _create_test_image(self, filename, format_type, size):
        """Helper to create test image."""
        img = Image.new('RGB', size, color='blue')
        img_io = BytesIO()
        img.save(img_io, format=format_type)
        img_io.seek(0)
        return SimpleUploadedFile(filename, img_io.getvalue(), content_type='image/jpeg')
    
    def test_resize_image_on_upload(self):
        """Test image resizing."""
        original_size = len(self.test_image.read())
        self.test_image.seek(0)
        
        resized = resize_image_on_upload(self.test_image, max_width=1000)
        self.assertIsNotNone(resized)
        
        # Verify resized image is smaller
        resized_size = len(resized.read())
        self.assertLess(resized_size, original_size)
    
    def test_compress_image(self):
        """Test image compression."""
        original_size = len(self.test_image.read())
        self.test_image.seek(0)
        
        compressed = compress_image(self.test_image, quality=85)
        self.assertIsNotNone(compressed)
        
        # Verify compressed image is smaller
        compressed_size = len(compressed.read())
        self.assertLess(compressed_size, original_size)
    
    def test_generate_webp_version(self):
        """Test WebP generation."""
        webp_content, webp_filename = generate_webp_version(self.test_image)
        
        self.assertIsNotNone(webp_content)
        self.assertIsNotNone(webp_filename)
        self.assertTrue(webp_filename.endswith('.webp'))
    
    def test_process_image_with_webp(self):
        """Test comprehensive image processing with WebP."""
        result = process_image_with_webp(self.test_image)
        
        self.assertTrue(result['original'] is not None)
        self.assertTrue(result['webp'] is not None)
        self.assertEqual(result['original_filename'], 'test.jpg')
        self.assertTrue(result['webp_filename'].endswith('.webp'))
        self.assertIsNotNone(result['dimensions'])
        self.assertGreater(result['original_size'], 0)
        self.assertGreater(result['webp_size'], 0)
    
    def test_optimize_image_for_web(self):
        """Test web optimization."""
        result = optimize_image_for_web(self.test_image)
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['original'])
        self.assertIsNotNone(result['webp'])
        self.assertIsNone(result['error'])


class ImageURLTests(TestCase):
    """Test image URL utilities."""
    
    def test_get_webp_image_url(self):
        """Test WebP URL generation."""
        original_url = '/media/universities/logos/logo.jpg'
        webp_url = get_webp_image_url(original_url)
        
        self.assertEqual(webp_url, '/media/universities/logos/logo.webp')
    
    def test_get_webp_image_url_png(self):
        """Test WebP URL generation for PNG."""
        original_url = '/media/articles/images/image.png'
        webp_url = get_webp_image_url(original_url)
        
        self.assertEqual(webp_url, '/media/articles/images/image.webp')
    
    def test_get_webp_image_url_none(self):
        """Test WebP URL generation with None."""
        webp_url = get_webp_image_url(None)
        self.assertIsNone(webp_url)
    
    def test_get_image_dimensions(self):
        """Test image dimension extraction."""
        img = Image.new('RGB', (800, 600), color='green')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        test_image = SimpleUploadedFile('test.jpg', img_io.getvalue(), content_type='image/jpeg')
        dimensions = get_image_dimensions(test_image)
        
        self.assertEqual(dimensions, (800, 600))


class ImageOptimizationIntegrationTests(TestCase):
    """Integration tests for image optimization."""
    
    def setUp(self):
        """Create test images."""
        self.test_image = self._create_test_image('test.jpg', 'JPEG', (3000, 2000))
    
    def _create_test_image(self, filename, format_type, size):
        """Helper to create test image."""
        img = Image.new('RGB', size, color='purple')
        img_io = BytesIO()
        img.save(img_io, format=format_type)
        img_io.seek(0)
        return SimpleUploadedFile(filename, img_io.getvalue(), content_type='image/jpeg')
    
    def test_full_optimization_pipeline(self):
        """Test complete optimization pipeline."""
        # Validate
        validate_image_upload(self.test_image)
        
        # Optimize
        result = optimize_image_for_web(self.test_image)
        
        # Verify
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['original'])
        self.assertIsNotNone(result['webp'])
        
        # Verify file size reduction
        original_size = result['original_size']
        webp_size = result['webp_size']
        
        # WebP should be smaller than original
        self.assertLess(webp_size, original_size)
    
    def test_optimization_without_webp(self):
        """Test optimization without WebP generation."""
        result = optimize_image_for_web(self.test_image, generate_webp=False)
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['original'])
        self.assertIsNone(result['webp'])
    
    def test_optimization_with_custom_quality(self):
        """Test optimization with custom quality setting."""
        result_high = optimize_image_for_web(self.test_image, quality=95)
        result_low = optimize_image_for_web(self.test_image, quality=70)
        
        # Higher quality should result in larger file
        self.assertGreater(result_high['original_size'], result_low['original_size'])
