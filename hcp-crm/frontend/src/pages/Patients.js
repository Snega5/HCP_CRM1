import React, { useCallback, useEffect, useState } from "react";
import Loader from "../components/Loader";
import Modal from "../components/Modal";
import ConfirmDialog from "../components/ConfirmDialog";
import PatientForm from "../components/PatientForm";
import PatientDetailModal from "../components/PatientDetailModal";
import { useNotify } from "../context/NotificationContext";
import { getErrorMessage } from "../services/api";
import { createPatient, deletePatient, listPatients, updatePatient } from "../services/patientService";

const PAGE_SIZE = 10;

export default function Patients() {
  const notify = useNotify();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState(""); // debounced search term
  const [page, setPage] = useState(0);
  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // modal state
  const [formPatient, setFormPatient] = useState(undefined); // undefined=closed, null=new, object=edit
  const [viewPatient, setViewPatient] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [busy, setBusy] = useState(false);

  // Debounce the search box so we don't call the API on every keystroke
  useEffect(() => {
    const t = setTimeout(() => {
      setQuery(search.trim());
      setPage(0);
    }, 350);
    return () => clearTimeout(t);
  }, [search]);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await listPatients({ q: query, skip: page * PAGE_SIZE, limit: PAGE_SIZE }));
    } catch (err) {
      setError(getErrorMessage(err, "Could not load patients"));
    } finally {
      setLoading(false);
    }
  }, [query, page]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSave = async (payload) => {
    setBusy(true);
    try {
      if (formPatient) {
        await updatePatient(formPatient.id, payload);
        notify.success("Patient updated");
      } else {
        await createPatient(payload);
        notify.success("Patient added");
      }
      setFormPatient(undefined);
      load();
    } catch (err) {
      notify.error(getErrorMessage(err, "Could not save patient"));
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    setBusy(true);
    try {
      await deletePatient(deleteTarget.id);
      notify.success("Patient deleted");
      setDeleteTarget(null);
      // If we deleted the last row on this page, go back one page
      if (data.items.length === 1 && page > 0) setPage(page - 1);
      else load();
    } catch (err) {
      notify.error(getErrorMessage(err, "Could not delete patient"));
    } finally {
      setBusy(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  return (
    <div className="patients-page">
      <div className="toolbar">
        <input
          className="input search-input"
          placeholder="Search by name, ID, diagnosis, doctor or phone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button className="btn btn-primary" onClick={() => setFormPatient(null)}>
          + Add patient
        </button>
      </div>

      <div className="card">
        {loading ? (
          <Loader text="Loading patients..." />
        ) : error ? (
          <div className="error-card">
            <p>{error}</p>
            <button className="btn btn-primary" onClick={load}>
              Retry
            </button>
          </div>
        ) : data.items.length === 0 ? (
          <div className="empty-state">
            {query ? `No patients match "${query}".` : "No patients yet. Click “Add patient” to create the first record."}
          </div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Age</th>
                  <th>Gender</th>
                  <th>Diagnosis</th>
                  <th>Doctor</th>
                  <th>Appointment</th>
                  <th className="right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((p) => (
                  <tr key={p.id}>
                    <td className="muted">{p.patient_code}</td>
                    <td className="strong">{p.full_name}</td>
                    <td>{p.age ?? "—"}</td>
                    <td>{p.gender || "—"}</td>
                    <td className="truncate">{p.diagnosis || "—"}</td>
                    <td>{p.doctor_assigned || "—"}</td>
                    <td>{p.appointment_date || "—"}</td>
                    <td className="right actions">
                      <button className="btn-link" onClick={() => setViewPatient(p)}>
                        View
                      </button>
                      <button className="btn-link" onClick={() => setFormPatient(p)}>
                        Edit
                      </button>
                      <button className="btn-link danger" onClick={() => setDeleteTarget(p)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && !error && data.total > 0 && (
          <div className="pagination">
            <span className="muted">
              {data.total} patient{data.total === 1 ? "" : "s"} · page {page + 1} of {totalPages}
            </span>
            <div>
              <button className="btn btn-ghost" disabled={page === 0} onClick={() => setPage(page - 1)}>
                Previous
              </button>{" "}
              <button className="btn btn-ghost" disabled={page + 1 >= totalPages} onClick={() => setPage(page + 1)}>
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {formPatient !== undefined && (
        <Modal title={formPatient ? "Edit patient" : "Add new patient"} onClose={() => !busy && setFormPatient(undefined)} wide>
          <PatientForm
            initialValues={formPatient || {}}
            onSubmit={handleSave}
            onCancel={() => setFormPatient(undefined)}
            submitLabel={formPatient ? "Save changes" : "Add patient"}
            loading={busy}
          />
        </Modal>
      )}

      {viewPatient && (
        <PatientDetailModal
          patient={viewPatient}
          onClose={() => setViewPatient(null)}
          onEdit={() => {
            setFormPatient(viewPatient);
            setViewPatient(null);
          }}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Delete patient"
          message={`Permanently delete ${deleteTarget.full_name} (${deleteTarget.patient_code})? This cannot be undone.`}
          loading={busy}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
