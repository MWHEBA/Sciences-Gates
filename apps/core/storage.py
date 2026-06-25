from django.contrib.staticfiles.storage import ManifestStaticFilesStorage

class SafeManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    Custom static files storage that does not raise an error
    when a static file is missing in the manifest.
    Instead, it falls back to the original unhashed file path.
    """
    manifest_strict = False

    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content, filename)
        except ValueError:
            # Fallback to original name if file is missing
            return name
