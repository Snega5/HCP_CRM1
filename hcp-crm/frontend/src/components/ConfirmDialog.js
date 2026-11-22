import React from "react";
import Modal from "./Modal";

export default function ConfirmDialog({ title, message, confirmLabel = "Delete", loading, onConfirm, onCancel }) {
  return (
    <Modal title={title} onClose={onCancel}>
      <p className="confirm-text">{message}</p>
      <div className="form-actions">
        <button className="btn btn-ghost" onClick={onCancel} disabled={loading}>
          Cancel
        </button>
        <button className="btn btn-danger" onClick={onConfirm} disabled={loading}>
          {loading ? "Working..." : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
