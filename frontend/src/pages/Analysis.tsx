import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import ImageUpload from "../components/ImageUpload";
import VoiceInput from "../components/VoiceInput";
import DiagnosisDisplay from "../components/DiagnosisDisplay";
import GraphVisualization from "../components/GraphVisualization";
import { useAnalysis } from "../hooks/useAnalysis";
import { useGraph } from "../hooks/useGraph";
import { DiagnosisResponse } from "../services/api";

const Analysis: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [textQuery, setTextQuery] = useState("");
  const { isLoading, result, error, analyzeImage, analyzeText, reset } = useAnalysis();
  const { graphData, updateGraph, clearGraph } = useGraph();

  const handleImageSelect = (selected: File) => {
    setFile(selected);
  };

  const handleAnalyze = async () => {
    clearGraph();
    let response: DiagnosisResponse | undefined;
    if (file) {
      response = await analyzeImage(file, textQuery || undefined);
    } else if (textQuery.trim()) {
      response = await analyzeText(textQuery);
    }
    if (response) {
      updateGraph(response);
    }
  };

  const handleVoiceTranscript = (text: string) => {
    setTextQuery(text);
  };

  const handleReset = () => {
    setFile(null);
    setTextQuery("");
    reset();
    clearGraph();
  };

  return (
    <div>
      <h2 style={{ marginTop: 0, color: "#2d6a4f" }}>{t("nav.analysis")}</h2>

      <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
        {/* Left panel: inputs */}
        <div style={{ flex: 1, minWidth: 320 }}>
          <ImageUpload onImageSelect={handleImageSelect} isLoading={isLoading} />

          <div style={{ marginTop: 16 }}>
            <VoiceInput onTranscript={handleVoiceTranscript} isProcessing={isLoading} />
          </div>

          <textarea
            value={textQuery}
            onChange={(e) => setTextQuery(e.target.value)}
            placeholder={i18n.language === "ar" ? "اكتب سؤالك هنا..." : "Type your question here..."}
            style={{
              width: "100%",
              minHeight: 80,
              marginTop: 16,
              padding: 12,
              borderRadius: 8,
              border: "1px solid #ddd",
              fontSize: 14,
              resize: "vertical",
              direction: i18n.language === "ar" ? "rtl" : "ltr",
              boxSizing: "border-box",
            }}
          />

          <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
            <button
              onClick={handleAnalyze}
              disabled={(!file && !textQuery.trim()) || isLoading}
              style={{
                flex: 1,
                padding: "12px 32px",
                backgroundColor: (!file && !textQuery.trim()) || isLoading ? "#ccc" : "#2d6a4f",
                color: "#fff",
                border: "none",
                borderRadius: 8,
                fontSize: 16,
                cursor: (!file && !textQuery.trim()) || isLoading ? "not-allowed" : "pointer",
              }}
            >
              {isLoading ? t("analysis.analyzing") : t("analysis.analyze")}
            </button>
            <button
              onClick={handleReset}
              style={{
                padding: "12px 24px",
                backgroundColor: "#fff",
                color: "#666",
                border: "1px solid #ddd",
                borderRadius: 8,
                fontSize: 14,
                cursor: "pointer",
              }}
            >
              {t("common.cancel")}
            </button>
          </div>

          {error && (
            <p style={{ color: "#d32f2f", marginTop: 12 }}>{error}</p>
          )}
        </div>

        {/* Right panel: results */}
        <div style={{ flex: 1, minWidth: 320 }}>
          <DiagnosisDisplay diagnosis={result} isLoading={isLoading} />

          <div style={{ marginTop: 24 }}>
            <GraphVisualization nodes={graphData.nodes} edges={graphData.edges} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analysis;
