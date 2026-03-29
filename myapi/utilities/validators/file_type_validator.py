import magic

ALLOWED_TYPES= {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}

def detect_file_type(uploaded_file):
    file_bytes= uploaded_file.read(2048)

    mime= magic.from_buffer(file_bytes, mime= True)

    uploaded_file.seek(0)

    if mime not in ALLOWED_TYPES:
        

        raise ValueError("Unsupported File type")
    
    return ALLOWED_TYPES[mime]