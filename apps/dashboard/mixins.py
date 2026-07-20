"""
Dashboard access control mixins for role-based authorization.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy


class DashboardMixin(LoginRequiredMixin):
    """
    Mixin requiring user to be logged in and have a profile.
    يتطلب من المستخدم أن يكون مسجل دخول وله ملف شخصي
    """
    login_url = 'dashboard:login'
    redirect_field_name = 'next'

    def _is_ajax(self):
        """Return whether the current request came from an XMLHttpRequest."""
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def dispatch(self, request, *args, **kwargs):
        """Check if user is authenticated and has a profile."""
        if not request.user.is_authenticated:
            # Redirect to login with next parameter
            from django.urls import reverse
            login_url = reverse(self.login_url)
            next_url = request.get_full_path()
            return redirect(f'{login_url}?next={next_url}')

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'لم يتم العثور على ملف المستخدم. يرجى التواصل مع المسؤول.')
            from django.urls import reverse
            login_url = reverse('dashboard:login')
            next_url = request.get_full_path()
            return redirect(f'{login_url}?next={next_url}')

        # Check if user is staff (access control)
        if not request.user.is_staff:
            messages.error(request, 'ليس لديك صلاحيات للوصول إلى لوحة التحكم.')
            from django.urls import reverse
            login_url = reverse('dashboard:login')
            next_url = request.get_full_path()
            return redirect(f'{login_url}?next={next_url}')

        return super().dispatch(request, *args, **kwargs)


class ContentAdminRequiredMixin(DashboardMixin):
    """
    Mixin requiring user to be Content Admin or Super Admin.
    يتطلب من المستخدم أن يكون مسؤول محتوى أو مسؤول نظام
    """

    def dispatch(self, request, *args, **kwargs):
        """Check if user has content admin or super admin role."""
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'profile'):
            messages.error(request, 'لم يتم العثور على ملف المستخدم. يرجى التواصل مع المسؤول.')
            return redirect('dashboard:login')

        user_profile = request.user.profile
        if not (user_profile.is_content_admin or user_profile.is_super_admin):
            messages.error(request, 'ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة. يرجى التواصل مع المسؤول.')
            return HttpResponseForbidden('غير مصرح بالوصول إلى هذا المورد')

        return super().dispatch(request, *args, **kwargs)


class SEOAdminRequiredMixin(DashboardMixin):
    """
    Mixin requiring user to be SEO Admin or Super Admin.
    يتطلب من المستخدم أن يكون مسؤول SEO أو مسؤول نظام
    """

    def dispatch(self, request, *args, **kwargs):
        """Check if user has SEO admin or super admin role."""
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'profile'):
            messages.error(request, 'لم يتم العثور على ملف المستخدم. يرجى التواصل مع المسؤول.')
            return redirect('dashboard:login')

        user_profile = request.user.profile
        if not (user_profile.is_seo_admin or user_profile.is_super_admin):
            messages.error(request, 'ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة. يرجى التواصل مع المسؤول.')
            return HttpResponseForbidden('غير مصرح بالوصول إلى هذا المورد')

        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(DashboardMixin):
    """
    Mixin requiring user to be Super Admin.
    يتطلب من المستخدم أن يكون مسؤول نظام
    """

    def dispatch(self, request, *args, **kwargs):
        """Check if user has super admin role."""
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'profile'):
            messages.error(request, 'لم يتم العثور على ملف المستخدم. يرجى التواصل مع المسؤول.')
            return redirect('dashboard:login')

        user_profile = request.user.profile
        if not user_profile.is_super_admin:
            messages.error(request, 'ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة. يرجى التواصل مع المسؤول.')
            return HttpResponseForbidden('غير مصرح بالوصول إلى هذا المورد')

        return super().dispatch(request, *args, **kwargs)
