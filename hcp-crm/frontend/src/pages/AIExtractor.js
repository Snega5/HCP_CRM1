import React, { useState } from "react";
import PatientForm from "../components/PatientForm";
import { useNotify } from "../context/NotificationContext";
import { getErrorMessage } from "../services/api";
import { extractPatientInfo } from "../services/extractorService";
import { createPatient } from "../services/patientService";

const SAMPLE =
  "Patient John, 45 years old, male, visited the hospital with fever and headache. Diagnosed with viral fever. Assigned to Dr. Kumar.";

const FIELD_KEYS = [
  "patient_name",
  "age",
  "gender",
  "phone",
  "email",
  "symptoms",
  "diagnosis",
  "medical_history",
  "doctor_assigned",
  "appointment_date",
];

export default function AIExtractor() {
  const notify = useNotify();
  const [text, setText] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null); // { extracted, model, runId }
  const [error, setError] = useState("");

  const handleExtract = async () => {
    if (text.trim().length < 10) {
      setError("Please enter at least a sentence of medical text.");
      return;
    }
    setExtracting(true);
    setError("");
    setResult(null);
    try {
      const data = await extractPatientInfo(text.trim());
      setResult({ ...data, runId: Date.now() });
    } catch (err) {
      setError(getErrorMessage(err, "Extraction failed"));
    } finally {
      setExtracting(false);
    }
  };

  const handleSave = async (payload) => {
    setSaving(true);
    try {
      await createPatient({ ...payload, source: "ai_extractor" });
      notify.success("Patient saved to the database");
      setResult(null);
      setText("");
    } catch (err) {
      notify.error(getErrorMessage(err, "Could not save patient"));
    } finally {
      setSaving(false);
    }
  };

  const handleClear = () => {
    setText("");
    setResult(null);
    setError("");
  };

  // Map the AI field names to the form field names
  const formValues = result
    ? { ...result.extracted, full_name: result.extracted.patient_name }
    : null;
  const found = result ? FIELD_KEYS.filter((k) => result.extracted[k] !== null && result.extracted[k] !== undefined).length : 0;

  return (
    <div className="extractor-page">
      <div className="card">
        <div className="card-header">
          <h3>1. Paste medical text</h3>
          <button className="btn-link" onClick={() => setText(SAMPLE)} disabled={extracting}>
            Use sample text
          </button>
        </div>
        <textarea
          className="input extractor-text"
          rows={8}
          maxLength={5000}
          placeholder="e.g. Patient John, 45 years old, male, visited the hospital with fever and headache. Diagnosed with viral fever. Assigned to Dr. Kumar."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={extracting}
        />
        <div className="extractor-footer">
          <span className="muted small">{text.length} / 5000 characters · use fictional data only</span>
          <div>
            <button className="btn btn-ghost" onClick={handleClear} disabled={extracting || (!text && !result)}>
              Clear
            </button>{" "}
            <button className="btn btn-primary" onClick={handleExtract} disabled={extracting || !text.trim()}>
              {extracting ? "Extracting..." : "✦ Extract Information"}
            </button>
          </div>
        </div>
        {extracting && (
          <div className="loader-wrap compact">
            <div className="spinner" />
            <span>Asking the AI to read the text...</span>
          </div>
        )}
        {error && <div className="inline-error">{error}</div>}
      </div>

      {result && (
        <div className="card">
          <div className="card-header">
            <h3>2. Review and edit, then save</h3>
            <span className="muted small">
              {found} of {FIELD_KEYS.length} fields found
            </span>
          </div>
          <div className="ai-banner">
            AI-generated result. Check every field against the original text. Fields that were not mentioned are left
            blank. Nothing is saved until you click <strong>Save patient</strong>.
          </div>
          <PatientForm
            key={result.runId}
            initialValues={formValues}
            onSubmit={handleSave}
            onCancel={() => setResult(null)}
            submitLabel="Save patient"
            loading={saving}
          />
          <details className="raw-json">
            <summary>View raw extracted JSON</summary>
            <pre>{JSON.stringify(result.extracted, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
}
