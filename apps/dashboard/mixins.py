"""
Dashboard access control mixins for role-based authorization.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy


def validate_dashboard_user(user):
    """
    Central helper to validate whether a user is an active, authenticated staff member with a valid profile.
    Returns (is_valid: bool, reason: str).
    """
    if not user or not user.is_authenticated:
        return False, 'user_unauthenticated'
    if not user.is_active:
        return False, 'user_inactive'
    if not getattr(user, 'is_staff', False):
        return False, 'not_staff'

    try:
        profile = getattr(user, 'profile', None)
        if profile is None:
            return False, 'missing_profile'
    except ObjectDoesNotExist:
        return False, 'missing_profile'

    return True, 'valid'


class DashboardMixin(LoginRequiredMixin):
    """
    Mixin requiring user to be logged in, active, staff, and have a valid profile.
    يتطلب من المستخدم أن يكون مسجل دخول ونشط وله صلاحية إدارة وملف شخصي سليم.
    """
    login_url = 'dashboard:login'
    redirect_field_name = 'next'

    def _is_ajax(self):
        """Return whether the current request came from an XMLHttpRequest or expects JSON."""
        return (
            self.request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            self.request.content_type == 'application/json' or
            'application/json' in self.request.META.get('HTTP_ACCEPT', '') or
            self.request.path.startswith('/sg/api/') or
            self.request.path.startswith('/api/')
        )

    def dispatch(self, request, *args, **kwargs):
        """Check if user is authenticated and meets dashboard access requirements."""
        # 1. Unauthenticated requests
        if not request.user.is_authenticated:
            if self._is_ajax():
                return JsonResponse({'error': 'Authentication required', 'authenticated': False}, status=401)

            login_url = reverse(self.login_url)
            next_url = request.get_full_path()
            # Prevent circular next parameter if current path is already the login page
            clean_next = next_url.split('?')[0].rstrip('/')
            if clean_next == login_url.rstrip('/'):
                return redirect(login_url)
            return redirect(f'{login_url}?next={next_url}')

        # 2. Authenticated user validation
        is_valid, reason = validate_dashboard_user(request.user)
        if not is_valid:
            if self._is_ajax():
                return JsonResponse({'error': 'Dashboard access denied', 'reason': reason}, status=403)

            # Cleanly terminate invalid / broken sessions to prevent redirect loops
            logout(request)
            if reason == 'not_staff':
                messages.error(request, 'ليس لديك صلاحيات للوصول إلى لوحة التحكم.')
            elif reason == 'missing_profile':
                messages.error(request, 'لم يتم العثور على ملف المستخدم. يرجى التواصل مع المسؤول.')
            elif reason == 'user_inactive':
                messages.error(request, 'تم تعطيل هذا الحساب. يرجى مراجعة إدارة النظام.')
            else:
                messages.error(request, 'جلسة العمل غير صالحة، يرجى تسجيل الدخول مرة أخرى.')

            return redirect(self.login_url)

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

        is_valid, _ = validate_dashboard_user(request.user)
        if not is_valid:
            return super().dispatch(request, *args, **kwargs)

        user_profile = request.user.profile
        if not (user_profile.is_content_admin or user_profile.is_super_admin or request.user.is_superuser):
            if self._is_ajax():
                return JsonResponse({'error': 'Permission denied: Content Admin role required'}, status=403)
            messages.warning(request, 'ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة.')
            if request.method == 'GET':
                return redirect('dashboard:home')
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

        is_valid, _ = validate_dashboard_user(request.user)
        if not is_valid:
            return super().dispatch(request, *args, **kwargs)

        user_profile = request.user.profile
        if not (user_profile.is_seo_admin or user_profile.is_super_admin or request.user.is_superuser):
            if self._is_ajax():
                return JsonResponse({'error': 'Permission denied: SEO Admin role required'}, status=403)
            messages.warning(request, 'ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة.')
            if request.method == 'GET':
                return redirect('dashboard:home')
            return HttpResponseForbidden('غير مصرح بالوصول إلى هذا المورد')

        return super().dispatch(request, *args, **kwargs)


class ContentOrSEOAdminRequiredMixin(DashboardMixin):
    """
    Mixin requiring user to be Content Admin, SEO Admin, or Super Admin.
    يتطلب من المستخدم أن يكون مسؤول محتوى، مسؤول SEO، أو مسؤول نظام
    """

    def dispatch(self, request, *args, **kwargs):
        """Check if user has content admin, SEO admin, or super admin role."""
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        is_valid, _ = validate_dashboard_user(request.user)
        if not is_valid:
            return super().dispatch(request, *args, **kwargs)

        user_profile = request.user.profile
        if not (user_profile.is_content_admin or user_profile.is_seo_admin or user_profile.is_super_admin or request.user.is_superuser):
            if self._is_ajax():
                return JsonResponse({'error': 'Permission denied: Content or SEO Admin role required'}, status=403)
            messages.warning(request, 'ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة.')
            if request.method == 'GET':
                return redirect('dashboard:home')
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

        is_valid, _ = validate_dashboard_user(request.user)
        if not is_valid:
            return super().dispatch(request, *args, **kwargs)

        user_profile = request.user.profile
        if not (user_profile.is_super_admin or request.user.is_superuser):
            if self._is_ajax():
                return JsonResponse({'error': 'Permission denied: Super Admin role required'}, status=403)
            messages.warning(request, 'ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة.')
            if request.method == 'GET':
                return redirect('dashboard:home')
            return HttpResponseForbidden('غير مصرح بالوصول إلى هذا المورد')

        return super().dispatch(request, *args, **kwargs)
