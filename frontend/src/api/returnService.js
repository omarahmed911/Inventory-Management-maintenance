import api from "./axios";

export const getSaleReturns = (params) => api.get("/returns/sales/", { params });
export const createSaleReturn = (data) => api.post("/returns/sales/create/", data);

export const getPurchaseReturns = (params) => api.get("/returns/purchases/", { params });
export const createPurchaseReturn = (data) => api.post("/returns/purchases/create/", data);
