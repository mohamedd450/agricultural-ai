import React, { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";

const Analysis: React.FC = () => {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type.startsWith("image/")) {
      setFile(dropped);
      setPreview(URL.createObjectURL(dropped));
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
    }
  };

  const handleAnalyze = () => {
    if (!file) return;
    setIsAnalyzing(true);
    // Placeholder for API call
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  return (
    <div>
      <h2 style={{ marginTop: 0, color: "#2d6a4f" }}>{t("nav.analysis")}</h2>

      {/* Upload area */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        style={{
          border: "2px dashed #52b788",
          borderRadius: 12,
          padding: 48,
          textAlign: "center",
          backgroundColor: "#fff",
          cursor: "pointer",
          marginBottom: 24,
        }}
      >
        {preview ? (
          <img
            src={preview}
            alt="Preview"
            style={{ maxWidth: 300, maxHeight: 300, borderRadius: 8 }}
          />
        ) : (
          <>
            <p style={{ fontSize: 18, color: "#2d6a4f", margin: 0 }}>
              {t("analysis.uploadImage")}
            </p>
            <p style={{ fontSize: 14, color: "#888", marginTop: 8 }}>
              {t("analysis.dragDrop")}
            </p>
          </>
        )}
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          style={{ display: "none" }}
          id="file-input"
        />
        <label
          htmlFor="file-input"
          style={{
            display: "inline-block",
            marginTop: 16,
            padding: "10px 24px",
            backgroundColor: "#2d6a4f",
            color: "#fff",
            borderRadius: 8,
            cursor: "pointer",
            fontSize: 14,
          }}
        >
          {t("analysis.uploadImage")}
        </label>
      </div>

      {/* Analyze button */}
      <button
        onClick={handleAnalyze}
        disabled={!file || isAnalyzing}
        style={{
          padding: "12px 32px",
          backgroundColor: file && !isAnalyzing ? "#2d6a4f" : "#ccc",
          color: "#fff",
          border: "none",
          borderRadius: 8,
          fontSize: 16,
          cursor: file && !isAnalyzing ? "pointer" : "not-allowed",
        }}
      >
        {isAnalyzing ? t("analysis.analyzing") : t("analysis.analyze")}
      </button>

      {/* Results placeholder */}
      {!file && (
        <p style={{ marginTop: 32, color: "#888", textAlign: "center" }}>
          {t("analysis.noResults")}
        </p>
      )}
    </div>
  );
};

export default Analysis;
