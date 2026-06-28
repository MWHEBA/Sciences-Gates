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


from django.core.files.storage import FileSystemStorage
import os

class SafeFileSystemStorage(FileSystemStorage):
    """
    Custom file system storage that safely handles file deletions
    on systems with ASCII filesystem encoding (like cPanel/Passenger).
    """
    def get_valid_name(self, name):
        """
        Ensure filenames are strictly ASCII-safe to prevent UnicodeEncodeError
        during file save operations on systems with ASCII filesystem encoding.
        """
        # Get standard clean filename from Django
        name = super().get_valid_name(name)
        
        # Split root and extension
        root, ext = os.path.splitext(name)
        ext = ext.lower()
        
        # Convert root to a safe ASCII-only slug
        from django.utils.text import slugify
        slug = slugify(root)
        
        if not slug:
            # Fallback for entirely non-ASCII names (like Arabic)
            import hashlib
            h = hashlib.md5(root.encode('utf-8', errors='ignore')).hexdigest()[:8]
            slug = f"file_{h}"
            
        return f"{slug}{ext}"

    def delete(self, name):
        try:
            super().delete(name)
        except UnicodeEncodeError:
            try:
                # Bypasses the UnicodeEncodeError by passing a bytes path to os.remove/os.rmdir
                path_bytes = self.path(name).encode('utf-8')
                if os.path.isdir(path_bytes):
                    os.rmdir(path_bytes)
                else:
                    os.remove(path_bytes)
            except Exception:
                pass
        except Exception:
            # Safely catch other exceptions (e.g. PermissionError) to prevent app crashes on file deletion
            pass


