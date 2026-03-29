from django.core.exceptions import ValidationError

def validate_file_size(value):
    # 10MB in bytes: 10 * 1024 * 1024
    filesize = value.size
    
    if filesize > 10485760:
        raise ValidationError("The maximum file size that can be uploaded is 10MB")
    return value
    