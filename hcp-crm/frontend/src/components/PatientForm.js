import React, { useState } from "react";

const EMPTY = {
  full_name: "",
  age: "",
  gender: "",
  phone: "",
  email: "",
  diagnosis: "",
  symptoms: "",
  medical_history: "",
  doctor_assigned: "",
  appointment_date: "",
};

// Convert API values (null) to form values (""), and form values back to API values (null)
const toForm = (p = {}) =>
  Object.keys(EMPTY).reduce((acc, k) => ({ ...acc, [k]: p[k] === null || p[k] === undefined ? "" : String(p[k]) }), {});

const toPayload = (f) => {
  const out = {};
  Object.keys(EMPTY).forEach((k) => {
    const v = typeof f[k] === "string" ? f[k].trim() : f[k];
    out[k] = v === "" ? null : v;
  });
  out.age = out.age === null ? null : Number(out.age);
  return out;
};

/**
 * Reusable patient form (also used by the AI extractor page in Stage 4).
 * Props: initialValues, onSubmit(payload), onCancel, submitLabel, loading
 */
export default function PatientForm({ initialValues, onSubmit, onCancel, submitLabel = "Save", loading = false }) {
  const [form, setForm] = useState(toForm(initialValues));

  const set = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    onSubmit(toPayload(form));
  };

  return (
    <form onSubmit={submit}>
      <div className="form-grid">
        <div className="form-group span-2">
          <label htmlFor="full_name">Full name *</label>
          <input id="full_name" name="full_name" className="input" value={form.full_name} onChange={set} required maxLength={120} />
        </div>

        <div className="form-group">
          <label htmlFor="age">Age</label>
          <input id="age" name="age" type="number" min="0" max="130" className="input" value={form.age} onChange={set} />
        </div>
        <div className="form-group">
          <label htmlFor="gender">Gender</label>
          <select id="gender" name="gender" className="input" value={form.gender} onChange={set}>
            <option value="">Not specified</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="phone">Phone number</label>
          <input id="phone" name="phone" className="input" value={form.phone} onChange={set} maxLength={30} />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input id="email" name="email" type="email" className="input" value={form.email} onChange={set} />
        </div>

        <div className="form-group">
          <label htmlFor="doctor_assigned">Doctor assigned</label>
          <input id="doctor_assigned" name="doctor_assigned" className="input" value={form.doctor_assigned} onChange={set} maxLength={120} />
        </div>
        <div className="form-group">
          <label htmlFor="appointment_date">Appointment date</label>
          <input id="appointment_date" name="appointment_date" type="date" className="input" value={form.appointment_date} onChange={set} />
        </div>

        <div className="form-group span-2">
          <label htmlFor="diagnosis">Diagnosis</label>
          <textarea id="diagnosis" name="diagnosis" className="input" rows={2} value={form.diagnosis} onChange={set} />
        </div>
        <div className="form-group span-2">
          <label htmlFor="symptoms">Symptoms</label>
          <textarea id="symptoms" name="symptoms" className="input" rows={2} value={form.symptoms} onChange={set} />
        </div>
        <div className="form-group span-2">
          <label htmlFor="medical_history">Medical history</label>
          <textarea id="medical_history" name="medical_history" className="input" rows={3} value={form.medical_history} onChange={set} />
        </div>
      </div>

      <div className="form-actions">
        {onCancel && (
          <button type="button" className="btn btn-ghost" onClick={onCancel} disabled={loading}>
            Cancel
          </button>
        )}
        <button className="btn btn-primary" disabled={loading}>
          {loading ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
