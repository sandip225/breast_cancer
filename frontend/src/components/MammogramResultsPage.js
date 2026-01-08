import React, { useState } from "react";
import { FiArrowLeft, FiArrowRight, FiDownload } from "react-icons/fi";
import DetectedRegionsPanel from "./DetectedRegionsPanel";
import "../App.css";

function MammogramResultsPage({
  side,
  results,
  onBack,
  onNext,
  onBackToUpload,
  showNextButton = true,
}) {
  const [visualTab, setVisualTab] = useState("overlay");
  const [detailsTab, setDetailsTab] = useState("clinical");
  const [isZoomed, setIsZoomed] = useState(false);
  const [selectedRegionId, setSelectedRegionId] = useState(null);
  const [regionCrops, setRegionCrops] = useState({});

  const zoomImageRef = React.useRef(null);

  const handleMouseMove = (e) => {
    if (!isZoomed) return;
    const img = zoomImageRef.current;
    if (!img) return;

    const rect = img.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    img.style.transformOrigin = `${x}% ${y}%`;
  };

  const handleImageClick = (e) => {
    const img = zoomImageRef.current;
    if (!img) return;

    if (isZoomed) {
      img.style.transform = "scale(1)";
      img.style.transformOrigin = "center center";
      setIsZoomed(false);
    } else {
      const rect = img.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      img.style.transformOrigin = `${x}% ${y}%`;
      img.style.transform = "scale(2.5)";
      setIsZoomed(true);
    }
  };

  const getActiveVisualImage = () => {
    switch (visualTab) {
      case "heatmap":
        return results.heatmap;
      case "bbox":
        return results.bbox;
      case "original":
        return results.cancer_type || results.original;
      case "overlay":
      default:
        return results.overlay;
    }
  };

  const getRiskClass = () => {
    const risk = results.risk?.toLowerCase() || "";
    if (risk.includes("very high risk")) {
      return "risk-high";
    } else if (risk.includes("high risk") && !risk.includes("moderate")) {
      return "risk-high";
    } else if (risk.includes("moderate")) {
      return "risk-moderate";
    } else if (risk.includes("very low risk")) {
      return "risk-low";
    } else if (risk.includes("low risk")) {
      return "risk-low";
    }
    return "";
  };

  const getResultClass = () => {
    const result = results.result?.toLowerCase() || "";
    if (result.includes("malignant") || result.includes("cancerous")) {
      return "result-malignant";
    } else if (result.includes("benign") || result.includes("non-cancerous")) {
      return "result-benign";
    }
    return "";
  };

  const sideTitle = side === "right" ? "Right Mammogram" : "Left Mammogram";
  const stepNumber = side === "right" ? "3 of 4" : "4 of 4";

  return (
    <main className="analysis-container">
      <section className="analysis-card">
        <div style={{ textAlign: "center", marginBottom: "20px" }}>
          <h2>{sideTitle} Analysis</h2>
          <p style={{ color: "#666", fontSize: "0.95rem" }}>Step {stepNumber}</p>
        </div>

        {/* Result Header */}
        <div
          className="result-header"
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            textAlign: "center",
          }}
        >
          <h2 className={`result-title ${getResultClass()}`}>
            {results.result || "Analysis Result"}
          </h2>
          <p className={`risk-pill ${getRiskClass()}`}>
            Risk Level:&nbsp;
            <strong>{results.risk || "Not available"}</strong>
          </p>
        </div>

        {/* Prediction Metrics Section */}
        <section className="section">
          <h3 className="section-title">Prediction Metrics</h3>
          <div className="metric-grid">
            <div className="metric">
              <span className="metric-label">Benign</span>
              <h3>
                {results.benign != null ? `${results.benign.toFixed(2)}%` : "—"}
              </h3>
            </div>
            <div className="metric">
              <span className="metric-label">Malignant</span>
              <h3>
                {results.malignant != null
                  ? `${results.malignant.toFixed(2)}%`
                  : "—"}
              </h3>
            </div>
            <div className="metric">
              <span className="metric-label">Model Confidence</span>
              <h3>
                {results.confidence != null
                  ? `${results.confidence.toFixed(2)}%`
                  : "—"}
              </h3>
            </div>
          </div>
        </section>

        {/* AI Summary Section */}
        <section className="section">
          <h3 className="section-title">AI Summary</h3>
          <div className="summary-box malignant">
            <p>{results.findings?.summary || "Analysis summary not available."}</p>
          </div>
        </section>

        {/* Visual Analysis Section */}
        <section className="section">
          <h3 className="section-title">Visual Analysis</h3>
          <p className="section-subtitle">
            Grad-CAM attention maps showing which regions influenced the model's
            decision.
          </p>

          <div className="visual-tabs">
            <button
              className={`visual-tab ${visualTab === "overlay" ? "active" : ""}`}
              onClick={() => setVisualTab("overlay")}
            >
              Heatmap Overlay
            </button>
            <button
              className={`visual-tab ${visualTab === "heatmap" ? "active" : ""}`}
              onClick={() => setVisualTab("heatmap")}
            >
              Heatmap Only
            </button>
            <button
              className={`visual-tab ${visualTab === "bbox" ? "active" : ""}`}
              onClick={() => setVisualTab("bbox")}
            >
              Region Detection (BBox)
            </button>
            <button
              className={`visual-tab ${visualTab === "original" ? "active" : ""}`}
              onClick={() => setVisualTab("original")}
            >
              Type of Cancer detection
            </button>
          </div>

          <div className="visual-panel">
            <div className="visual-image-card" style={{ position: "relative" }}>
              {getActiveVisualImage() ? (
                <>
                  <div
                    className="zoom-container"
                    onMouseMove={handleMouseMove}
                    onClick={handleImageClick}
                    style={{ position: "relative" }}
                  >
                    {results.view_analysis && results.view_analysis.view_code && (
                      <div
                        style={{
                          position: "absolute",
                          top: "12px",
                          left: "12px",
                          background:
                            "linear-gradient(135deg, rgba(0, 0, 0, 0.85) 0%, rgba(0, 0, 0, 0.75) 100%)",
                          color: "white",
                          padding: "10px 18px",
                          borderRadius: "8px",
                          fontWeight: "700",
                          fontSize: "1.1rem",
                          zIndex: 10,
                          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.4)",
                          backdropFilter: "blur(10px)",
                          border: "2px solid rgba(255, 255, 255, 0.2)",
                          display: "flex",
                          flexDirection: "column",
                          gap: "4px",
                        }}
                      >
                        <div
                          style={{
                            fontSize: "1.3rem",
                            letterSpacing: "1px",
                            color: "#00D9FF",
                            textShadow: "0 0 10px rgba(0, 217, 255, 0.5)",
                          }}
                        >
                          {results.view_analysis.view_code} View
                        </div>
                        <div
                          style={{
                            fontSize: "0.75rem",
                            fontWeight: "500",
                            color: "rgba(255, 255, 255, 0.85)",
                            letterSpacing: "0.5px",
                          }}
                        >
                          {results.view_analysis.view_code.includes("MLO")
                            ? "Mediolateral Oblique: Angled side view"
                            : "Craniocaudal: Top-to-bottom view"}
                        </div>
                      </div>
                    )}

                    <img
                      ref={zoomImageRef}
                      src={getActiveVisualImage()}
                      alt="Visual analysis"
                      style={{
                        cursor: isZoomed ? "zoom-out" : "zoom-in",
                      }}
                    />
                  </div>
                </>
              ) : (
                <p className="muted small">Image not available.</p>
              )}
            </div>

            {/* Detected Regions Panel */}
            <DetectedRegionsPanel
              regions={results.findings?.regions || []}
              regionCrops={regionCrops}
              selectedRegionId={selectedRegionId}
              onRegionSelect={(id) => setSelectedRegionId(id)}
              onRegionHover={(id) => setSelectedRegionId(id)}
              onRegionLeave={() => setSelectedRegionId(null)}
            />
          </div>
        </section>

        {/* Detailed Analysis Information */}
        <div className="results-info-card">
          <h4>Understanding Your Results</h4>

          {/* Comprehensive Image Analysis Section */}
          {results.findings?.comprehensive_analysis && (
            <div style={{ marginBottom: "24px" }}>
              <p
                className="regions-header"
                style={{ marginBottom: "16px", fontSize: "1.1rem" }}
              >
                📊 Comprehensive Image Analysis
              </p>

              {/* Breast Density */}
              {results.findings.comprehensive_analysis.breast_density && (
                <div
                  style={{
                    padding: "14px",
                    background:
                      "linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)",
                    borderRadius: "12px",
                    boxShadow: "0 2px 8px rgba(21, 101, 192, 0.15)",
                    marginBottom: "12px",
                  }}
                >
                  <div
                    style={{
                      fontWeight: "700",
                      color: "#1565C0",
                      marginBottom: "10px",
                      fontSize: "0.95rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <span style={{ fontSize: "1.1rem" }}>🔬</span> Breast
                    Density (ACR BI-RADS)
                  </div>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "8px",
                      fontSize: "0.85rem",
                    }}
                  >
                    <div
                      style={{
                        padding: "6px 8px",
                        background: "rgba(255,255,255,0.6)",
                        borderRadius: "6px",
                      }}
                    >
                      <span style={{ color: "#666" }}>Category:</span>{" "}
                      <strong style={{ color: "#1565C0" }}>
                        Type{" "}
                        {
                          results.findings.comprehensive_analysis.breast_density
                            .category
                        }
                      </strong>
                    </div>
                    <div
                      style={{
                        padding: "6px 8px",
                        background: "rgba(255,255,255,0.6)",
                        borderRadius: "6px",
                      }}
                    >
                      <span style={{ color: "#666" }}>Density:</span>{" "}
                      <strong style={{ color: "#1565C0" }}>
                        {
                          results.findings.comprehensive_analysis.breast_density
                            .density_percentage
                        }
                        %
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Tissue Texture */}
              {results.findings.comprehensive_analysis.tissue_texture && (
                <div
                  style={{
                    padding: "14px",
                    background:
                      "linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%)",
                    borderRadius: "12px",
                    boxShadow: "0 2px 8px rgba(123, 31, 162, 0.15)",
                    marginBottom: "12px",
                  }}
                >
                  <div
                    style={{
                      fontWeight: "700",
                      color: "#7B1FA2",
                      marginBottom: "10px",
                      fontSize: "0.95rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <span style={{ fontSize: "1.1rem" }}>🧬</span> Tissue
                    Texture Analysis
                  </div>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "8px",
                      fontSize: "0.85rem",
                    }}
                  >
                    <div
                      style={{
                        padding: "6px 8px",
                        background: "rgba(255,255,255,0.6)",
                        borderRadius: "6px",
                      }}
                    >
                      <span style={{ color: "#666" }}>Pattern:</span>{" "}
                      <strong style={{ color: "#7B1FA2" }}>
                        {
                          results.findings.comprehensive_analysis.tissue_texture
                            .pattern
                        }
                      </strong>
                    </div>
                    <div
                      style={{
                        padding: "6px 8px",
                        background: "rgba(255,255,255,0.6)",
                        borderRadius: "6px",
                      }}
                    >
                      <span style={{ color: "#666" }}>Uniformity:</span>{" "}
                      <strong style={{ color: "#7B1FA2" }}>
                        {
                          results.findings.comprehensive_analysis.tissue_texture
                            .uniformity_score
                        }
                        %
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Symmetry Analysis */}
              {results.findings.comprehensive_analysis.symmetry && (
                <div
                  style={{
                    padding: "14px",
                    background:
                      "linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)",
                    borderRadius: "12px",
                    boxShadow: "0 2px 8px rgba(46, 125, 50, 0.15)",
                    marginBottom: "12px",
                  }}
                >
                  <div
                    style={{
                      fontWeight: "700",
                      color: "#2E7D32",
                      marginBottom: "10px",
                      fontSize: "0.95rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <span style={{ fontSize: "1.1rem" }}>⚖️</span> Symmetry
                  </div>
                  <div
                    style={{
                      display: "grid",
                      gap: "6px",
                      fontSize: "0.85rem",
                    }}
                  >
                    <div
                      style={{
                        padding: "6px 8px",
                        background: "rgba(255,255,255,0.6)",
                        borderRadius: "6px",
                      }}
                    >
                      <span style={{ color: "#666" }}>Assessment:</span>{" "}
                      <strong style={{ color: "#2E7D32" }}>
                        {results.findings.comprehensive_analysis.symmetry.assessment}
                      </strong>
                    </div>
                    <div
                      style={{
                        padding: "6px 8px",
                        background: "rgba(255,255,255,0.6)",
                        borderRadius: "6px",
                      }}
                    >
                      <span style={{ color: "#666" }}>Score:</span>{" "}
                      <strong style={{ color: "#2E7D32" }}>
                        {results.findings.comprehensive_analysis.symmetry.symmetry_score}
                        %
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Detected Regions Summary */}
              {results.findings?.regions && results.findings.regions.length > 0 && (
                <div
                  style={{
                    padding: "14px",
                    background:
                      "linear-gradient(135deg, #FFE0B2 0%, #FFCC80 100%)",
                    borderRadius: "12px",
                    boxShadow: "0 2px 8px rgba(230, 124, 115, 0.15)",
                    marginBottom: "12px",
                  }}
                >
                  <div
                    style={{
                      fontWeight: "700",
                      color: "#E65100",
                      marginBottom: "10px",
                      fontSize: "0.95rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <span style={{ fontSize: "1.1rem" }}>🎯</span> Detected
                    Regions
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "#333" }}>
                    <strong>Total Regions:</strong>{" "}
                    {results.findings.regions.length}
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "#333" }}>
                    <strong>High Confidence:</strong>{" "}
                    {results.findings.regions.filter((r) => r.confidence > 0.75)
                      .length}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* View-Specific Analysis */}
          {results.view_analysis && (
            <div style={{ marginBottom: "24px" }}>
              <p
                className="regions-header"
                style={{ marginBottom: "16px", fontSize: "1.1rem" }}
              >
                📍 Mammogram View Analysis
              </p>
              <div
                style={{
                  padding: "14px",
                  background:
                    "linear-gradient(135deg, #E1F5FE 0%, #B3E5FC 100%)",
                  borderRadius: "12px",
                  boxShadow: "0 2px 8px rgba(3, 155, 229, 0.15)",
                }}
              >
                <div
                  style={{
                    fontWeight: "700",
                    color: "#0277BD",
                    marginBottom: "10px",
                    fontSize: "0.95rem",
                  }}
                >
                  View Type: {results.view_analysis.view_type}
                </div>
                <div style={{ fontSize: "0.85rem", color: "#333" }}>
                  <strong>Laterality:</strong> {results.view_analysis.laterality}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div
          style={{
            display: "flex",
            gap: "15px",
            marginTop: "30px",
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          <button
            className="btn-primary"
            onClick={onBackToUpload}
            style={{ display: "flex", alignItems: "center", gap: "8px" }}
          >
            <FiArrowLeft size={18} />
            Back to Upload
          </button>

          {showNextButton && side === "right" && (
            <button
              className="btn-primary"
              onClick={onNext}
              style={{ display: "flex", alignItems: "center", gap: "8px" }}
            >
              Next: Left Mammogram
              <FiArrowRight size={18} />
            </button>
          )}

          {side === "left" && (
            <button
              className="btn-primary"
              onClick={onBack}
              style={{ display: "flex", alignItems: "center", gap: "8px" }}
            >
              <FiArrowLeft size={18} />
              Back: Right Mammogram
            </button>
          )}
        </div>
      </section>
    </main>
  );
}

export default MammogramResultsPage;
