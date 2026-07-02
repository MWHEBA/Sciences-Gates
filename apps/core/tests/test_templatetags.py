from django.test import TestCase
from django.core.paginator import Paginator
from apps.core.templatetags.table_tags import elided_page_range, get_item

class TableTagsFilterTestCase(TestCase):
    """
    Test cases for custom template filters in table_tags.py.
    """
    def test_get_item_dict_string_key(self):
        """Test get_item with a dictionary and string keys."""
        data = {'name': 'Science Gates', 'type': 'Institute'}
        self.assertEqual(get_item(data, 'name'), 'Science Gates')
        self.assertEqual(get_item(data, 'nonexistent'), '')

    def test_get_item_dict_int_key(self):
        """Test get_item with a dictionary and integer keys (resolving the reported bug)."""
        data = {1: 'One', 2: 'Two', 0: 'Zero'}
        self.assertEqual(get_item(data, 1), 'One')
        self.assertEqual(get_item(data, 0), 'Zero')
        self.assertEqual(get_item(data, 3), '')

    def test_get_item_nested_dot_notation(self):
        """Test get_item with nested dot notation."""
        class Profile:
            def __init__(self):
                self.email = 'test@example.com'

        class User:
            def __init__(self):
                self.profile = Profile()

        data = {
            'user': User(),
            'info': {
                'city': 'Cairo',
                'zip': 12345
            }
        }
        self.assertEqual(get_item(data, 'user.profile.email'), 'test@example.com')
        self.assertEqual(get_item(data, 'info.city'), 'Cairo')
        self.assertEqual(get_item(data, 'info.nonexistent'), '')
        self.assertEqual(get_item(data, 'user.profile.nonexistent'), '')

    def test_get_item_list_index(self):
        """Test get_item with list index lookup."""
        data = ['first', 'second', 'third']
        self.assertEqual(get_item(data, 0), 'first')
        self.assertEqual(get_item(data, 1), 'second')
        self.assertEqual(get_item(data, 5), '')  # Out of range index should return empty string

    def test_get_item_object_attribute(self):
        """Test get_item with standard object attribute lookup."""
        class Dummy:
            def __init__(self):
                self.title = 'Hello'

        dummy = Dummy()
        self.assertEqual(get_item(dummy, 'title'), 'Hello')
        self.assertEqual(get_item(dummy, 'nonexistent'), '')

    def test_get_item_edge_cases(self):
        """Test get_item with edge cases like empty inputs or None values."""
        self.assertEqual(get_item(None, 'key'), '')
        self.assertEqual(get_item({'key': 'val'}, None), '')
        self.assertEqual(get_item({'key': 'val'}, ''), '')

    def test_elided_page_range_valid(self):
        """Test that elided_page_range correctly generates the elided page list."""
        # Create a paginator with 100 items, 10 items per page (10 pages total)
        paginator = Paginator(list(range(100)), 10)
        
        # Test for page 1
        page1 = paginator.page(1)
        # on_each_side=2, on_ends=1
        # Page range: [1, 2, 3, paginator.ELLIPSIS, 10]
        pages_list = list(elided_page_range(page1))
        self.assertEqual(pages_list, [1, 2, 3, paginator.ELLIPSIS, 10])
        
        # Test for page 5
        page5 = paginator.page(5)
        # Page range: [1, 2, 3, 4, 5, 6, 7, paginator.ELLIPSIS, 10]
        # (Page 2 is not elided because only a single page is between 1 and 3)
        pages_list = list(elided_page_range(page5))
        self.assertEqual(pages_list, [1, 2, 3, 4, 5, 6, 7, paginator.ELLIPSIS, 10])

    def test_elided_page_range_none(self):
        """Test that elided_page_range returns an empty list if page_obj is None."""
        self.assertEqual(elided_page_range(None), [])

    def test_elided_page_range_exception(self):
        """Test that elided_page_range falls back to full range on exception."""
        # Create a mock object that will cause an exception when get_elided_page_range is called
        class FakePage:
            def __init__(self):
                self.number = 1
                self.paginator = FakePaginator()
                
        class FakePaginator:
            def __init__(self):
                self.page_range = [1, 2, 3]
            def get_elided_page_range(self, *args, **kwargs):
                raise ValueError("Simulated error")
                
        self.assertEqual(elided_page_range(FakePage()), [1, 2, 3])
