# -*- coding: utf-8 -*-
"""
Tests for core app utilities and models.
"""
from io import BytesIO
from PIL import Image
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.conf import settings


class ImageValidationTestCase(TestCase):
    """Test cases for image validation utilities."""
    
    def setUp(self):
        """Import models in setUp to avoid module-level imports."""
        from apps.core.utils import (
            validate_image_file_size,
            validate_image_format,
            validate_image_dimensions,
            validate_image_upload,
            resize_image_on_upload,
            compress_image,
            get_image_dimensions,
        )
        self.validate_image_file_size = validate_image_file_size
        self.validate_image_format = validate_image_format
        self.validate_image_dimensions = validate_image_dimensions
        self.validate_image_upload = validate_image_upload
        self.resize_image_on_upload = resize_image_on_upload
        self.compress_image = compress_image
        self.get_image_dimensions = get_image_dimensions
    
    def create_test_image(self, width=800, height=600, format='JPEG', size_kb=None):
        """
        Helper method to create a test image.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            format: Image format (JPEG, PNG, GIF)
            size_kb: If specified, create image with approximate size in KB
            
        Returns:
            SimpleUploadedFile: Test image file
        """
        img = Image.new('RGB', (width, height), color='red')
        img_io = BytesIO()
        
        # Adjust quality to control file size if needed
        quality = 85
        if size_kb:
            # Estimate quality needed for target size
            quality = max(10, min(95, int(85 * (100 / size_kb))))
        
        img.save(img_io, format=format, quality=quality)
        img_io.seek(0)
        
        filename = f'test_image.{format.lower()}'
        return SimpleUploadedFile(
            filename,
            img_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    def test_validate_image_file_size_valid(self):
        """Test that valid file size passes validation."""
        # Create 2MB image (under 5MB limit)
        image = self.create_test_image(size_kb=2048)
        # Should not raise exception
        self.validate_image_file_size(image)
    
    def test_validate_image_file_size_too_large(self):
        """Test that oversized file fails validation."""
        # Create image larger than 5MB
        image = self.create_test_image()
        # Manually set size to exceed limit
        image.size = settings.MAX_UPLOAD_SIZE + 1
        
        with self.assertRaises(ValidationError) as context:
            self.validate_image_file_size(image)
        
        self.assertIn('حجم الملف كبير جداً', str(context.exception))
    
    def test_validate_image_format_valid_jpeg(self):
        """Test that JPEG format passes validation."""
        image = self.create_test_image(format='JPEG')
        # Should not raise exception
        self.validate_image_format(image)
    
    def test_validate_image_format_valid_png(self):
        """Test that PNG format passes validation."""
        image = self.create_test_image(format='PNG')
        # Should not raise exception
        self.validate_image_format(image)
    
    def test_validate_image_format_invalid_extension(self):
        """Test that invalid file extension fails validation."""
        image = self.create_test_image(format='JPEG')
        image.name = 'test_image.txt'
        
        with self.assertRaises(ValidationError) as context:
            self.validate_image_format(image)
        
        self.assertIn('صيغة الملف غير مدعومة', str(context.exception))
    
    def test_validate_image_dimensions_valid(self):
        """Test that valid dimensions pass validation."""
        image = self.create_test_image(width=800, height=600)
        # Should not raise exception
        self.validate_image_dimensions(image)
    
    def test_validate_image_dimensions_too_small(self):
        """Test that too-small dimensions fail validation."""
        image = self.create_test_image(width=50, height=50)
        
        with self.assertRaises(ValidationError) as context:
            self.validate_image_dimensions(image)
        
        self.assertIn('الصورة صغيرة جداً', str(context.exception))
    
    def test_validate_image_upload_comprehensive(self):
        """Test comprehensive image validation."""
        image = self.create_test_image(width=1200, height=800)
        # Should not raise exception
        self.validate_image_upload(image)
    
    def test_resize_image_on_upload_no_resize_needed(self):
        """Test that image smaller than max width is not resized."""
        image = self.create_test_image(width=800, height=600)
        original_size = image.size
        
        resized = self.resize_image_on_upload(image, max_width=1920)
        
        # Resized image should exist and be valid
        self.assertIsNotNone(resized)
        self.assertGreater(resized.size, 0)
    
    def test_resize_image_on_upload_resize_needed(self):
        """Test that oversized image is resized."""
        image = self.create_test_image(width=3000, height=2000)
        
        resized = self.resize_image_on_upload(image, max_width=1920)
        
        # Resized image should be smaller
        self.assertLess(resized.size, image.size)
    
    def test_compress_image(self):
        """Test image compression."""
        image = self.create_test_image(width=1200, height=800)
        original_size = image.size
        
        compressed = self.compress_image(image, quality=75)
        
        # Compressed image should be smaller
        self.assertLess(compressed.size, original_size)
    
    def test_get_image_dimensions(self):
        """Test getting image dimensions."""
        image = self.create_test_image(width=800, height=600)
        
        width, height = self.get_image_dimensions(image)
        
        self.assertEqual(width, 800)
        self.assertEqual(height, 600)


class ImageUploadIntegrationTestCase(TestCase):
    """Integration tests for image upload workflow."""
    
    def setUp(self):
        """Import utilities in setUp."""
        from apps.core.utils import (
            validate_image_upload,
            resize_image_on_upload,
            get_image_dimensions,
        )
        self.validate_image_upload = validate_image_upload
        self.resize_image_on_upload = resize_image_on_upload
        self.get_image_dimensions = get_image_dimensions
    
    def create_test_image(self, width=800, height=600, format='JPEG'):
        """Helper to create test image."""
        img = Image.new('RGB', (width, height), color='blue')
        img_io = BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        
        filename = f'test_image.{format.lower()}'
        return SimpleUploadedFile(
            filename,
            img_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    def test_full_upload_workflow(self):
        """Test complete image upload and processing workflow."""
        # Create test image
        image = self.create_test_image(width=2400, height=1800)
        
        # Validate
        self.validate_image_upload(image)
        
        # Resize
        image.seek(0)
        resized = self.resize_image_on_upload(image, max_width=1920)
        
        # Verify resized image is valid
        width, height = self.get_image_dimensions(resized)
        self.assertLessEqual(width, 1920)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)


class UserProfileTestCase(TestCase):
    """Test cases for UserProfile model and role management."""
    
    def setUp(self):
        """Set up test fixtures."""
        from django.contrib.auth.models import User
        self.User = User
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_profile_auto_created_on_user_creation(self):
        """Test that UserProfile is automatically created when User is created."""
        # Create a new user
        new_user = self.User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        
        # Check that profile was created
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertIsNotNone(new_user.profile)
        self.assertEqual(new_user.profile.user, new_user)
    
    def test_user_profile_default_role_is_content_admin(self):
        """Test that default role is CONTENT_ADMIN."""
        from apps.core.models import UserRole
        profile = self.user.profile
        
        self.assertEqual(profile.role, UserRole.CONTENT_ADMIN)
        self.assertEqual(profile.get_role_display(), '\u0645\u0633\u0624\u0648\u0644 \u0627\u0644\u0645\u062d\u062a\u0648\u0649')
    
    def test_is_super_admin_method(self):
        """Test is_super_admin property."""
        from apps.core.models import UserRole
        profile = self.user.profile
        
        # Initially should be False
        self.assertFalse(profile.is_super_admin)
        
        # Change role to SUPER_ADMIN
        profile.role = UserRole.SUPER_ADMIN
        profile.save()
        
        # Refresh from database
        profile.refresh_from_db()
        self.assertTrue(profile.is_super_admin)
    
    def test_is_content_admin_method(self):
        """Test is_content_admin property."""
        from apps.core.models import UserRole
        profile = self.user.profile
        
        # Should be True by default
        self.assertTrue(profile.is_content_admin)
        
        # Change role to SEO_ADMIN
        profile.role = UserRole.SEO_ADMIN
        profile.save()
        
        # Refresh from database
        profile.refresh_from_db()
        self.assertFalse(profile.is_content_admin)
    
    def test_is_seo_admin_method(self):
        """Test is_seo_admin property."""
        from apps.core.models import UserRole
        profile = self.user.profile
        
        # Initially should be False
        self.assertFalse(profile.is_seo_admin)
        
        # Change role to SEO_ADMIN
        profile.role = UserRole.SEO_ADMIN
        profile.save()
        
        # Refresh from database
        profile.refresh_from_db()
        self.assertTrue(profile.is_seo_admin)
    
    def test_user_profile_string_representation(self):
        """Test __str__ method of UserProfile."""
        profile = self.user.profile
        
        expected_str = f'{self.user.username} - \u0645\u0633\u0624\u0648\u0644 \u0627\u0644\u0645\u062d\u062a\u0648\u0649'
        self.assertEqual(str(profile), expected_str)
    
    def test_user_profile_timestamps(self):
        """Test that created_at and updated_at timestamps are set."""
        import datetime
        profile = self.user.profile
        
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)
        self.assertAlmostEqual(profile.created_at, profile.updated_at, delta=datetime.timedelta(seconds=2))
    
    def test_user_profile_updated_at_changes_on_update(self):
        """Test that updated_at changes when profile is updated."""
        import time
        profile = self.user.profile
        original_updated_at = profile.updated_at
        
        # Wait a bit to ensure timestamp difference
        time.sleep(0.1)
        
        # Update profile
        from apps.core.models import UserRole
        profile.role = UserRole.SEO_ADMIN
        profile.save()
        
        # Refresh from database
        profile.refresh_from_db()
        
        # updated_at should be newer
        self.assertGreater(profile.updated_at, original_updated_at)
    
    def test_all_user_roles_available(self):
        """Test that all three user roles are available."""
        from apps.core.models import UserRole
        roles = [choice[0] for choice in UserRole.choices]
        
        self.assertIn(UserRole.SUPER_ADMIN, roles)
        self.assertIn(UserRole.CONTENT_ADMIN, roles)
        self.assertIn(UserRole.SEO_ADMIN, roles)
        self.assertEqual(len(roles), 3)
    
    def test_user_profile_one_to_one_relationship(self):
        """Test that UserProfile has OneToOne relationship with User."""
        # Create another user
        user2 = self.User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        # Each user should have exactly one profile
        self.assertEqual(self.user.profile.user, self.user)
        self.assertEqual(user2.profile.user, user2)
        
        # Profiles should be different
        self.assertNotEqual(self.user.profile, user2.profile)
    
    def test_user_profile_role_change(self):
        """Test changing user role."""
        from apps.core.models import UserRole
        profile = self.user.profile
        
        # Start as CONTENT_ADMIN
        self.assertEqual(profile.role, UserRole.CONTENT_ADMIN)
        
        # Change to SUPER_ADMIN
        profile.role = UserRole.SUPER_ADMIN
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.role, UserRole.SUPER_ADMIN)
        
        # Change to SEO_ADMIN
        profile.role = UserRole.SEO_ADMIN
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.role, UserRole.SEO_ADMIN)
    
    def test_user_profile_verbose_names(self):
        """Test that verbose names are set correctly."""
        profile = self.user.profile
        
        # Check model verbose names
        self.assertEqual(profile._meta.verbose_name, '\u0645\u0644\u0641 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645')
        self.assertEqual(profile._meta.verbose_name_plural, '\u0645\u0644\u0641\u0627\u062a \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645\u064a\u0646')
    
    def test_user_profile_role_field_choices(self):
        """Test that role field has correct choices."""
        from apps.core.models import UserRole
        profile = self.user.profile
        role_field = profile._meta.get_field('role')
        
        choices = dict(role_field.choices)
        self.assertEqual(choices[UserRole.SUPER_ADMIN], '\u0645\u0633\u0624\u0648\u0644 \u0627\u0644\u0646\u0638\u0627\u0645')
        self.assertEqual(choices[UserRole.CONTENT_ADMIN], '\u0645\u0633\u0624\u0648\u0644 \u0627\u0644\u0645\u062d\u062a\u0648\u0649')
        self.assertEqual(choices[UserRole.SEO_ADMIN], '\u0645\u0633\u0624\u0648\u0644 SEO')


class MediaFileTestCase(TestCase):
    """Test cases for MediaFile model properties and methods."""
    
    def test_file_extension_property(self):
        """Test that file_extension property returns the correct uppercase extension."""
        from apps.core.models import MediaFile
        
        # Case 1: Simple extension
        media_1 = MediaFile(original_filename='test_image.png')
        self.assertEqual(media_1.file_extension, 'PNG')
        
        # Case 2: Extension with multiple dots
        media_2 = MediaFile(original_filename='my.cool.photo.webp')
        self.assertEqual(media_2.file_extension, 'WEBP')
        
        # Case 3: Mixed case extension
        media_3 = MediaFile(original_filename='ANOTHER_IMAGE.JpEg')
        self.assertEqual(media_3.file_extension, 'JPEG')
        
        # Case 4: No extension
        media_4 = MediaFile(original_filename='no_extension')
        self.assertEqual(media_4.file_extension, '')
        
        # Case 5: Empty filename, fallback to file.name
        media_5 = MediaFile(original_filename='')
        media_5.file.name = 'fallback_path/image.svg'
        self.assertEqual(media_5.file_extension, 'SVG')
        
        # Case 6: PDF extension
        media_6 = MediaFile(original_filename='document.pdf')
        self.assertEqual(media_6.file_extension, 'PDF')

    def test_completion_score_property(self):
        """Test that completion_score property returns correct score (0-4)."""
        from apps.core.models import MediaFile
        
        # Case 1: 0 fields filled
        media = MediaFile(alt_text='', caption='', title='', description='')
        self.assertEqual(media.completion_score, 0)
        
        # Case 2: 1 field filled
        media.alt_text = 'Alt Text'
        self.assertEqual(media.completion_score, 1)
        
        # Case 3: 2 fields filled
        media.caption = 'Caption text'
        self.assertEqual(media.completion_score, 2)
        
        # Case 4: 3 fields filled
        media.title = 'Title text'
        self.assertEqual(media.completion_score, 3)
        
        # Case 5: 4 fields filled
        media.description = 'Description text'
        self.assertEqual(media.completion_score, 4)



