import React, { useState, useEffect } from "react";
import { createSaleReturn, createPurchaseReturn } from "../../api/returnService";

const ReturnModal = ({ open, type = "sale", record, onClose, onSuccess }) => {
  const [items, setItems] = useState([]);
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (record && record.items) {
      setItems(
        record.items.map((item) => ({
          id: item.id,
          product: item.product,
          product_name: item.product_name,
          max_qty: Number(item.quantity) || 0,
          return_qty: 0,
          price: Number(item.per_item_price || item.price || 0),
        }))
      );
      setReason("");
      setError("");
    }
  }, [record, open]);

  if (!open || !record) return null;

  const isSale = type === "sale";
  const refNo = isSale ? record.invoice_no : record.purchase_no;

  const handleQtyChange = (index, value) => {
    const val = parseFloat(value) || 0;
    setItems((prev) =>
      prev.map((it, idx) => (idx === index ? { ...it, return_qty: val } : it))
    );
  };

  const handlePriceChange = (index, value) => {
    const val = parseFloat(value) || 0;
    setItems((prev) =>
      prev.map((it, idx) => (idx === index ? { ...it, price: val } : it))
    );
  };

  const totalRefund = items.reduce(
    (sum, it) => sum + (it.return_qty > 0 ? it.return_qty * it.price : 0),
    0
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const returnItems = items
      .filter((it) => it.return_qty > 0)
      .map((it) => ({
        [isSale ? "sale_item" : "purchase_item"]: it.id,
        product: it.product,
        quantity: it.return_qty,
        refund_price: it.price,
      }));

    if (returnItems.length === 0) {
      setError("Please specify a return quantity greater than 0 for at least one item.");
      return;
    }

    // Check max quantities
    for (const it of items) {
      if (it.return_qty > it.max_qty) {
        setError(`Cannot return ${it.return_qty} of ${it.product_name}. Max available: ${it.max_qty}.`);
        return;
      }
    }

    setLoading(true);
    try {
      const payload = {
        [isSale ? "sale" : "purchase"]: record.id,
        total_refund_amount: totalRefund,
        reason: reason,
        items: returnItems,
      };

      if (isSale) {
        await createSaleReturn(payload);
      } else {
        await createPurchaseReturn(payload);
      }

      setLoading(false);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setLoading(false);
      const data = err.response?.data;
      const msg = data?.error || (data?.items ? JSON.stringify(data.items) : "Failed to process return.");
      setError(msg);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(15, 23, 42, 0.6)",
        backdropFilter: "blur(4px)",
        zIndex: 1050,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "#ffffff",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "680px",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "24px",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.2)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="d-flex justify-content-between align-items-center mb-3">
          <div>
            <h5 className="font-bold text-slate-800 m-0">
              Process {isSale ? "Sale Return (Credit Note)" : "Purchase Return (Debit Note)"}
            </h5>
            <p className="text-muted text-sm m-0">Ref: #{refNo}</p>
          </div>
          <button
            type="button"
            className="btn-close"
            aria-label="Close"
            onClick={onClose}
          />
        </div>

        {error && (
          <div className="alert alert-danger py-2 text-sm mb-3">
            <i className="bi bi-exclamation-triangle-fill me-2" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="table-responsive mb-3">
            <table className="table table-bordered table-sm align-middle text-sm">
              <thead className="table-light">
                <tr>
                  <th>Product</th>
                  <th className="text-end">Original Qty</th>
                  <th style={{ width: "120px" }}>Return Qty</th>
                  <th style={{ width: "120px" }}>Refund Price</th>
                  <th className="text-end">Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {items.map((it, idx) => (
                  <tr key={idx}>
                    <td className="fw-semibold">{it.product_name}</td>
                    <td className="text-end">{it.max_qty}</td>
                    <td>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max={it.max_qty}
                        className="form-control form-control-sm"
                        value={it.return_qty || ""}
                        placeholder="0"
                        onChange={(e) => handleQtyChange(idx, e.target.value)}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        className="form-control form-control-sm"
                        value={it.price || ""}
                        onChange={(e) => handlePriceChange(idx, e.target.value)}
                      />
                    </td>
                    <td className="text-end fw-bold">
                      ₹ {(it.return_qty * it.price).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="d-flex justify-content-between align-items-center mb-3 p-3 bg-light rounded">
            <span className="fw-bold">Total Refund Amount:</span>
            <span className="fs-5 fw-extrabold text-primary">₹ {totalRefund.toFixed(2)}</span>
          </div>

          <div className="mb-3">
            <label className="form-label fw-semibold text-sm">Reason for Return</label>
            <textarea
              className="form-control text-sm"
              rows={2}
              placeholder="e.g. Defective items, customer cancellation, excess delivery"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </div>

          <div className="d-flex justify-content-end gap-2">
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary btn-sm px-4 fw-bold"
              disabled={loading}
            >
              {loading ? "Processing..." : "Submit Return"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ReturnModal;
