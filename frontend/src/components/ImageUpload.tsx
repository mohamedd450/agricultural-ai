import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useTranslation } from "react-i18next";

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  isLoading: boolean;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ACCEPTED_TYPES: Record<string, string[]> = {
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/webp": [".webp"],
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: "100%",
    maxWidth: 480,
    margin: "0 auto",
  },
  dropzone: {
    border: "2px dashed #94a3b8",
    borderRadius: 12,
    padding: 32,
    textAlign: "center",
    cursor: "pointer",
    transition: "border-color 0.2s, background-color 0.2s",
    backgroundColor: "#f8fafc",
    minHeight: 200,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
  },
  dropzoneActive: {
    borderColor: "#22c55e",
    backgroundColor: "#f0fdf4",
  },
  dropzoneDisabled: {
    opacity: 0.6,
    cursor: "not-allowed",
  },
  icon: {
    fontSize: 48,
    color: "#64748b",
  },
  label: {
    fontSize: 16,
    fontWeight: 600,
    color: "#334155",
  },
  hint: {
    fontSize: 13,
    color: "#94a3b8",
  },
  preview: {
    width: "100%",
    maxHeight: 320,
    objectFit: "contain" as const,
    borderRadius: 8,
    marginTop: 12,
  },
  removeBtn: {
    marginTop: 8,
    padding: "6px 16px",
    border: "1px solid #e2e8f0",
    borderRadius: 6,
    background: "#fff",
    color: "#ef4444",
    cursor: "pointer",
    fontSize: 14,
  },
  error: {
    color: "#ef4444",
    fontSize: 13,
    marginTop: 8,
  },
};

const ImageUpload: React.FC<ImageUploadProps> = ({ onImageSelect, isLoading }) => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === "ar";
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: { errors: { code: string }[] }[]) => {
      setError(null);
      if (rejectedFiles.length > 0) {
        const firstError = rejectedFiles[0].errors[0]?.code;
        if (firstError === "file-too-large") {
          setError("File exceeds 10MB limit");
        } else if (firstError === "file-invalid-type") {
          setError("Only JPG, PNG, and WebP images are accepted");
        } else {
          setError("Invalid file");
        }
        return;
      }

      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        const url = URL.createObjectURL(file);
        setPreview(url);
        onImageSelect(file);
      }
    },
    [onImageSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    disabled: isLoading,
  });

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (preview) {
      URL.revokeObjectURL(preview);
    }
    setPreview(null);
    setError(null);
  };

  const dropzoneStyle: React.CSSProperties = {
    ...styles.dropzone,
    ...(isDragActive ? styles.dropzoneActive : {}),
    ...(isLoading ? styles.dropzoneDisabled : {}),
    direction: isRTL ? "rtl" : "ltr",
  };

  return (
    <div style={styles.container}>
      <div {...getRootProps()} style={dropzoneStyle}>
        <input {...getInputProps()} />

        {preview ? (
          <>
            <img src={preview} alt="Preview" style={styles.preview} />
            {!isLoading && (
              <button type="button" onClick={handleRemove} style={styles.removeBtn}>
                ✕ {t("common.cancel")}
              </button>
            )}
          </>
        ) : (
          <>
            <div style={styles.icon}>📷</div>
            <div style={styles.label}>{t("analysis.uploadImage")}</div>
            <div style={styles.hint}>{t("analysis.dragDrop")}</div>
            <div style={styles.hint}>JPG, PNG, WebP · max 10MB</div>
          </>
        )}

        {isLoading && (
          <div style={styles.hint}>{t("analysis.analyzing")}</div>
        )}
      </div>

      {error && <div style={styles.error}>{error}</div>}
    </div>
  );
};

export default ImageUpload;
