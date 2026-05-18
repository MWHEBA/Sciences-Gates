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

    def dispatch(self, request, *args, **kwargs):
        """Check if user is authenticated and has a profile."""
        if not request.user.is_authenticated:
            return redirect(self.login_url)

        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'لم يتم العثور على ملف المستخدم. يرجى التواصل مع المسؤول.')
            return redirect('dashboard:login')

        return super().dispatch(request, *args, **kwargs)


class ContentAdminRequiredMixin(DashboardMixin):
    """
    Mixin requiring user to be Content Admin or Super Admin.
    يتطلب من المستخدم أن يكون مسؤول محتوى أو مسؤول نظام
    """

    def dispatch(self, request, *args, **kwargs):
        """Check if user has content admin or super admin role."""
        response = super().dispatch(request, *args, **kwargs)

        # If parent dispatch returned a redirect, return it
        if isinstance(response, redirect.__class__):
            return response

        user_profile = request.user.profile
        if not (user_profile.is_content_admin() or user_profile.is_super_admin()):
            messages.error(request, 'ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة. يرجى التواصل مع المسؤول.')
            return HttpResponseForbidden('غير مصرح بالوصول إلى هذا المورد')

        return response


class SEOAdminRequiredMixin(DashboardMixin):
    """
    Mixin requiring user to be SEO Admin or Super Admin.
    يتطلب من المستخدم أن يكون مسؤول SEO أو مسؤول نظام
    """

    def dispatch(self, request, *args, **kwargs):
        """Check if user has SEO admin or super admin role."""
        response = super().dispatch(request, *args, **kwargs)

        # If parent dispatch returned a redirect, return it
        if isinstance(response, redirect.__class__):
            return response

        user_profile = request.user.profile
        if not (user_profile.is_seo_admin() or user_profile.is_super_admin()):
            messages.error(request, 'ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة. يرجى التواصل مع المسؤول.')
            return HttpResponseForbidden('غير مصرح بالوصول إلى هذا المورد')

        return response


class SuperAdminRequiredMixin(DashboardMixin):
    """
    Mixin requiring user to be Super Admin.
    يتطلب من المستخدم أن يكون مسؤول نظام
    """

    def dispatch(self, request, *args, **kwargs):
        """Check if user has super admin role."""
        response = super().dispatch(request, *args, **kwargs)

        # If parent dispatch returned a redirect, return it
        if isinstance(response, redirect.__class__):
            return response

        user_profile = request.user.profile
        if not user_profile.is_super_admin():
            messages.error(request, 'ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة. يرجى التواصل مع المسؤول.')
            return HttpResponseForbidden('غير مصرح بالوصول إلى هذا المورد')

        return response
