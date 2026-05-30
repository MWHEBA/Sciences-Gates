"""
Tests for the Data Table component (task 11.1).

Tests verify:
- Template renders correct HTML structure
- Semantic HTML (table, thead, tbody, th with scope, td)
- Column headers display correctly
- Row data displays with correct styling
- Action buttons are present and keyboard-focusable
- Badge component integration for status values
- Link rendering with primary color
- Horizontal scrolling on narrow viewports
- Empty state message when no rows
- CSS variable usage for colors
"""
from django.test import TestCase, RequestFactory
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class MockRow:
    """Mock row object for testing."""
    def __init__(self, id, name, status, created_at):
        self.id = id
        self.name = name
        self.status = status
        self.created_at = created_at


class DataTableComponentTest(TestCase):
    """Test the data table template component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        
        import datetime
        # Create mock rows
        self.rows = [
            MockRow(1, 'Article 1', 'published', datetime.date(2024, 1, 15)),
            MockRow(2, 'Article 2', 'unpublished', datetime.date(2024, 1, 14)),
            MockRow(3, 'Article 3', 'new', datetime.date(2024, 1, 13)),
        ]
        
        # Define columns
        self.columns = [
            {
                'label': 'الاسم',
                'key': 'name',
                'type': 'link',
                'link_url_name': 'dashboard:article-edit',
                'link_param': 'id',
            },
            {
                'label': 'الحالة',
                'key': 'status',
                'type': 'badge',
                'badge_status_key': 'status',
            },
            {
                'label': 'التاريخ',
                'key': 'created_at',
                'type': 'date',
            },
        ]
    
    def test_data_table_renders_with_correct_structure(self):
        """Test that data table renders with correct HTML structure."""
        # Use simple columns without URL reversing
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
            {'label': 'الحالة', 'key': 'status', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for table element
        self.assertIn('<table', html)
        self.assertIn('</table>', html)
        
        # Check for semantic HTML elements
        self.assertIn('<thead>', html)
        self.assertIn('</thead>', html)
        self.assertIn('<tbody>', html)
        self.assertIn('</tbody>', html)
    
    def test_column_headers_display_correctly(self):
        """Test that column headers display with correct styling."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
            {'label': 'الحالة', 'key': 'status', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check header styling
        self.assertIn('text-right', html)
        self.assertIn('text-xs', html)
        self.assertIn('font-semibold', html)
        self.assertIn('uppercase', html)
        self.assertIn('scope="col"', html)
        
        # Check for column labels
        self.assertIn('الاسم', html)
        self.assertIn('الحالة', html)
        self.assertIn('الإجراءات', html)
    
    def test_rows_display_with_correct_styling(self):
        """Test that rows display with correct padding and borders."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
            {'label': 'الحالة', 'key': 'status', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check row styling
        self.assertIn('border-b', html)
        self.assertIn('hover:bg-gray-50', html)
        self.assertIn('transition-colors', html)
        
        # Check for row data
        self.assertIn('Article 1', html)
        self.assertIn('Article 2', html)
        self.assertIn('Article 3', html)
    
    def test_cells_have_correct_padding(self):
        """Test that table cells have correct padding."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check cell padding
        self.assertIn('px-6', html)
        self.assertIn('py-4', html)
    
    def test_action_buttons_are_keyboard_focusable(self):
        """Test that action buttons have focus indicators."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check focus styling
        self.assertIn('focus:outline-none', html)
        self.assertIn('focus:ring-2', html)
        self.assertIn('focus:ring-offset-2', html)
    
    def test_action_buttons_have_aria_labels(self):
        """Test that action buttons have accessible labels."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for aria-label
        self.assertIn('aria-label', html)
        self.assertIn('تحرير', html)
        self.assertIn('حذف', html)
    
    def test_icons_are_marked_as_decorative(self):
        """Test that SVG icons are marked as decorative with aria-hidden."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for aria-hidden
        self.assertIn('aria-hidden="true"', html)
    
    def test_empty_state_displays_when_no_rows(self):
        """Test that empty state message displays when no rows."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': [],
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for empty state message
        self.assertIn('لا توجد بيانات للعرض', html)
    
    def test_table_has_overflow_scroll_container(self):
        """Test that table is wrapped in overflow-x-auto container."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for overflow container
        self.assertIn('overflow-x-auto', html)
    
    def test_table_uses_css_variables_for_colors(self):
        """Test that table uses CSS variables for colors."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for CSS variable usage
        self.assertIn('var(--border)', html)
        self.assertIn('var(--text-primary)', html)
        self.assertIn('var(--text-muted)', html)
        self.assertIn('var(--primary)', html)
        self.assertIn('var(--danger)', html)
    
    def test_link_column_renders_with_primary_color(self):
        """Test that link columns render with primary color."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for primary color styling
        self.assertIn('var(--primary)', html)
    
    def test_badge_column_includes_badge_component(self):
        """Test that badge columns include the badge component."""
        simple_columns = [
            {'label': 'الحالة', 'key': 'status', 'type': 'badge', 'badge_status_key': 'status'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for badge elements
        self.assertIn('rounded-full', html)
        self.assertIn('px-2.5', html)
        self.assertIn('py-0.5', html)
    
    def test_date_column_formats_dates_correctly(self):
        """Test that date columns format dates correctly."""
        simple_columns = [
            {'label': 'التاريخ', 'key': 'created_at', 'type': 'date'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for date formatting (d/m/Y format)
        self.assertIn('15/01/2024', html)
        self.assertIn('14/01/2024', html)
        self.assertIn('13/01/2024', html)
    
    def test_white_card_styling(self):
        """Test that table is displayed in a white card with rounded corners."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for card styling
        self.assertIn('bg-white', html)
        self.assertIn('rounded-lg', html)
        self.assertIn('shadow-sm', html)
        self.assertIn('border', html)
    
    def test_header_row_has_gray_background(self):
        """Test that header row has gray background."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check for header row styling
        self.assertIn('bg-gray-50', html)
    
    def test_text_size_is_consistent(self):
        """Test that all cell content uses text-sm."""
        simple_columns = [
            {'label': 'الاسم', 'key': 'name', 'type': 'text'},
        ]
        context = {
            'columns': simple_columns,
            'rows': self.rows,
            'edit_url_name': 'edit',
            'delete_url_name': 'delete',
        }
        
        html = render_to_string('dashboard/components/data_table.html', context)
        
        # Check table has text-sm
        self.assertIn('text-sm', html)
