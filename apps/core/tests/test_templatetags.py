from django.test import TestCase
from django.core.paginator import Paginator
from apps.core.templatetags.table_tags import elided_page_range

class TableTagsFilterTestCase(TestCase):
    """
    Test cases for custom template filters in table_tags.py.
    """
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
