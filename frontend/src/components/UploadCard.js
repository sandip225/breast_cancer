import React from "react";
import { FaUpload } from "react-icons/fa";

function UploadCard({ setFile }) {
  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setFile(e.target.files[0]);
      analyzeFile(e.target.files[0]);

    }
  };

  return (
    <div className="upload-card">
      <h3>Upload mammogram (DICOM)</h3>
      <p>Limit 200MB per file • DICOM</p>

      <div className="dropzone">
        <FaUpload size={32} style={{ marginBottom: "10px", color: "#AE70AF" }} />
        <p>Drag and drop file here</p>
        <input type="file" onChange={handleFileChange} />
        <button className="btn-primary">Browse File</button>
      </div>
    </div>
  );
}

export default UploadCard;