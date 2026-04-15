import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useTranslation } from 'react-i18next';
import { Upload, X, Image as ImageIcon } from 'lucide-react';

interface ImageUploadProps {
  onUpload: (files: File[]) => void;
  loading?: boolean;
}

const ImageUpload: React.FC<ImageUploadProps> = ({ onUpload, loading = false }) => {
  const { t } = useTranslation();
  const [previews, setPreviews] = useState<{ file: File; url: string }[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newPreviews = acceptedFiles.map((file) => ({
      file,
      url: URL.createObjectURL(file),
    }));
    setPreviews((prev) => [...prev, ...newPreviews]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxSize: 10 * 1024 * 1024,
    multiple: true,
  });

  const removePreview = (index: number) => {
    setPreviews((prev) => {
      const updated = [...prev];
      URL.revokeObjectURL(updated[index].url);
      updated.splice(index, 1);
      return updated;
    });
  };

  const handleUpload = () => {
    if (previews.length > 0) {
      onUpload(previews.map((p) => p.file));
    }
  };

  const dropzoneStyle: React.CSSProperties = {
    border: `2px dashed ${isDragActive ? '#2d6a4f' : '#ced4da'}`,
    borderRadius: 12,
    padding: 40,
    textAlign: 'center',
    cursor: 'pointer',
    background: isDragActive ? '#f0faf4' : '#fafafa',
    transition: 'all 0.2s',
  };

  const previewContainerStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 12,
    marginTop: 16,
  };

  const previewStyle: React.CSSProperties = {
    position: 'relative',
    width: 120,
    height: 120,
    borderRadius: 8,
    overflow: 'hidden',
    border: '1px solid #dee2e6',
  };

  return (
    <div>
      <div {...getRootProps()} style={dropzoneStyle}>
        <input {...getInputProps()} />
        <Upload size={40} color={isDragActive ? '#2d6a4f' : '#adb5bd'} />
        <p style={{ marginTop: 12, color: '#495057', fontWeight: 500 }}>
          {t('upload.dragDrop')}
        </p>
        <p style={{ marginTop: 4, fontSize: 13, color: '#868e96' }}>
          {t('upload.supportedFormats')}
        </p>
      </div>

      {previews.length > 0 && (
        <>
          <div style={previewContainerStyle}>
            {previews.map((preview, index) => (
              <div key={preview.url} style={previewStyle}>
                <img
                  src={preview.url}
                  alt={`${t('upload.preview')} ${index + 1}`}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removePreview(index);
                  }}
                  style={{
                    position: 'absolute',
                    top: 4,
                    right: 4,
                    background: 'rgba(0,0,0,0.6)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    width: 24,
                    height: 24,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    padding: 0,
                  }}
                  aria-label={t('upload.remove')}
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
          <button
            onClick={handleUpload}
            disabled={loading}
            style={{
              marginTop: 16,
              padding: '10px 24px',
              background: loading ? '#adb5bd' : '#2d6a4f',
              color: 'white',
              border: 'none',
              borderRadius: 8,
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: 14,
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <ImageIcon size={16} />
            {loading ? t('upload.uploading') : t('upload.upload')}
          </button>
        </>
      )}
    </div>
  );
};

export default ImageUpload;
