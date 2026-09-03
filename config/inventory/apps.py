from django.apps import AppConfig


class InventoryConfig(AppConfig):
    name = 'inventory'

    def ready(self):
        # Replace Django's password hash renderer with a masked display
        try:
            from django.utils.html import format_html
            from django.utils.translation import gettext as _

            def _masked_render_password_as_hash(value):
                if not value:
                    return format_html("<p><strong>{}</strong></p>", _("No password set."))
                return format_html("<p><strong>{}</strong>: {}</p>", _("Password"), "********")

            # Patch admin utils (used when displaying fields in admin)
            import django.contrib.admin.utils as admin_utils

            admin_utils.render_password_as_hash = _masked_render_password_as_hash

            # Also patch the original template tag module to be safe
            import django.contrib.auth.templatetags.auth as auth_tags

            auth_tags.render_password_as_hash = _masked_render_password_as_hash
        except Exception:
            # Fail quietly if imports aren't available yet
            pass
