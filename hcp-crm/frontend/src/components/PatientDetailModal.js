import React from "react";
import Modal from "./Modal";

const fmtDate = (d) => (d ? new Date(d + "T00:00:00").toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "—");

function Field({ label, value, full }) {
  return (
    <div className={`detail-field ${full ? "span-2" : ""}`}>
      <div className="detail-label">{label}</div>
      <div className="detail-value">{value || "—"}</div>
    </div>
  );
}

export default function PatientDetailModal({ patient, onClose, onEdit }) {
  return (
    <Modal title={`${patient.full_name}  ·  ${patient.patient_code || ""}`} onClose={onClose} wide>
      <div className="detail-grid">
        <Field label="Age" value={patient.age} />
        <Field label="Gender" value={patient.gender} />
        <Field label="Phone" value={patient.phone} />
        <Field label="Email" value={patient.email} />
        <Field label="Doctor assigned" value={patient.doctor_assigned} />
        <Field label="Appointment date" value={fmtDate(patient.appointment_date)} />
        <Field label="Diagnosis" value={patient.diagnosis} full />
        <Field label="Symptoms" value={patient.symptoms} full />
        <Field label="Medical history" value={patient.medical_history} full />
        <Field label="Added via" value={patient.source === "ai_extractor" ? "AI extractor" : "Manual entry"} />
        <Field label="Created" value={patient.created_at ? new Date(patient.created_at).toLocaleString() : ""} />
      </div>
      <div className="form-actions">
        <button className="btn btn-ghost" onClick={onClose}>
          Close
        </button>
        <button className="btn btn-primary" onClick={onEdit}>
          Edit patient
        </button>
      </div>
    </Modal>
  );
}
