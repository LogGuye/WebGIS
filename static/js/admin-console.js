const adminMetaScript = document.getElementById("adminMeta");
if (!adminMetaScript) {
  throw new Error("Không tìm thấy dữ liệu meta cho admin console.");
}
const adminMeta = JSON.parse(adminMetaScript.textContent || "{}");
const endpoints = adminMeta.endpoints || {};
const collectionUrl = endpoints.collection;
const detailUrl = (id) => `${collectionUrl}${id}/`;

const state = {
  editingId: null,
  properties: [],
  total: 0,
};

const tableBody = document.querySelector("[data-admin='properties-body']");
const totalLabel = document.querySelector("[data-admin='total']");
const searchInput = document.getElementById("admin-search");
const refreshButton = document.getElementById("admin-refresh");
const form = document.getElementById("admin-property-form");
const formTitle = document.getElementById("admin-form-title");
const resetButton = document.querySelector("[data-admin='reset']");
const toast = document.querySelector("[data-admin='toast']");
const inputs = {
  title: document.getElementById("admin-field-title"),
  description: document.getElementById("admin-field-description"),
  propertyType: document.getElementById("admin-field-property-type"),
  status: document.getElementById("admin-field-status"),
  price: document.getElementById("admin-field-price"),
  area: document.getElementById("admin-field-area"),
  address: document.getElementById("admin-field-address"),
  lat: document.getElementById("admin-field-lat"),
  lng: document.getElementById("admin-field-lng"),
  agent: document.getElementById("admin-field-agent"),
  featured: document.getElementById("admin-field-featured"),
};

const getCookie = (name) => {
  const cookieValue = document.cookie
    .split(";")
    .map((segment) => segment.trim())
    .find((segment) => segment.startsWith(`${name}=`));
  if (!cookieValue) {
    return null;
  }
  return decodeURIComponent(cookieValue.split("=")[1]);
};

const csrfToken = getCookie("csrftoken");
let toastTimer; // eslint-disable-line no-unused-vars
let searchTimer;

const showToast = (message, variant = "success") => {
  if (!toast) return;
  toast.textContent = message;
  toast.className = "admin-toast";
  toast.classList.add("active", variant);
  if (toastTimer) {
    clearTimeout(toastTimer);
  }
  toastTimer = setTimeout(() => {
    toast.classList.remove("active", "success", "error");
  }, 4000);
};

const formatPrice = (value) => {
  if (value == null || Number.isNaN(Number(value))) {
    return "—";
  }
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(Number(value));
};

const renderTable = () => {
  if (!tableBody) return;
  if (!state.properties.length) {
    tableBody.innerHTML = "<tr><td colspan='7' class='text-muted'>Không có dữ liệu (hoặc chưa đúng bộ lọc).</td></tr>";
    totalLabel.textContent = `Đang hiển thị 0/${state.total || 0} bản ghi`;
    return;
  }
  const rows = state.properties
    .map((prop) => {
      const agent = prop.agent ? prop.agent.name : "—";
      return `
        <tr data-id="${prop.id}">
          <td>${prop.id}</td>
          <td>${prop.title}</td>
          <td>${prop.property_type_label || prop.property_type}</td>
          <td>${prop.listing_status_label || prop.listing_status}</td>
          <td>${formatPrice(prop.price)}</td>
          <td>${agent}</td>
          <td class="admin-table-actions">
            <button type="button" data-action="edit">Sửa</button>
            <button type="button" data-action="delete">Xóa</button>
          </td>
        </tr>
      `;
    })
    .join("");
  tableBody.innerHTML = rows;
  totalLabel.textContent = `Đang hiển thị ${state.properties.length}/${state.total || state.properties.length} bản ghi`;
};

const loadProperties = async (query = "") => {
  if (!collectionUrl) {
    return;
  }
  const params = new URLSearchParams({ query });
  const url = `${collectionUrl}?${params.toString()}`;
  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
    },
    credentials: "same-origin",
  });
  if (!response.ok) {
    showToast("Không thể tải dữ liệu.", "error");
    return;
  }
  const payload = await response.json();
  state.properties = payload.results || [];
  state.total = payload.total || state.properties.length;
  renderTable();
};

const resetForm = () => {
  form.reset();
  state.editingId = null;
  formTitle.textContent = "Tạo tin mới";
};

const fillForm = (property) => {
  if (!property) return;
  state.editingId = property.id;
  formTitle.textContent = `Chỉnh sửa #${property.id}`;
  inputs.title.value = property.title;
  inputs.description.value = property.description || "";
  inputs.propertyType.value = property.property_type;
  inputs.status.value = property.listing_status;
  inputs.price.value = property.price || "";
  inputs.area.value = property.area || "";
  inputs.address.value = property.address || "";
  inputs.lat.value = property.lat ?? "";
  inputs.lng.value = property.lng ?? "";
  inputs.featured.checked = Boolean(property.is_featured);
  inputs.agent.value = property.agent ? property.agent.id : "";
};

const serializeForm = () => ({
  title: inputs.title.value.trim(),
  description: inputs.description.value.trim(),
  property_type: inputs.propertyType.value,
  listing_status: inputs.status.value,
  price: inputs.price.value,
  area: inputs.area.value,
  address: inputs.address.value.trim(),
  lat: inputs.lat.value || undefined,
  lng: inputs.lng.value || undefined,
  agent_id: inputs.agent.value || undefined,
  is_featured: inputs.featured.checked,
});

const performSave = async () => {
  const method = state.editingId ? "PUT" : "POST";
  const url = state.editingId ? detailUrl(state.editingId) : collectionUrl;
  const payload = serializeForm();
  const response = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
      Accept: "application/json",
    },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    showToast(errorPayload.error || "Lỗi khi lưu.", "error");
    return;
  }
  showToast(state.editingId ? "Đã cập nhật." : "Đã tạo bản ghi.");
  resetForm();
  loadProperties(searchInput.value.trim());
};

const deleteProperty = async (id) => {
  if (!id) return;
  if (!confirm("Xác nhận xóa tin này?")) {
    return;
  }
  const response = await fetch(detailUrl(id), {
    method: "DELETE",
    headers: {
      "X-CSRFToken": csrfToken,
      Accept: "application/json",
    },
    credentials: "same-origin",
  });
  if (!response.ok) {
    showToast("Không thể xóa.", "error");
    return;
  }
  showToast("Đã xóa tin.");
  if (state.editingId === Number(id)) {
    resetForm();
  }
  loadProperties(searchInput.value.trim());
};

form.addEventListener("submit", (event) => {
  event.preventDefault();
  performSave();
});

resetButton.addEventListener("click", () => {
  resetForm();
});

tableBody.addEventListener("click", (event) => {
  const action = event.target.dataset.action;
  const row = event.target.closest("tr");
  const id = row?.dataset.id;
  if (!action || !id) return;
  const numericId = Number(id);
  if (action === "edit") {
    const record = state.properties.find((item) => item.id === numericId);
    if (record) {
      startEditing(record);
    }
    return;
  }
  if (action === "delete") {
    deleteProperty(numericId);
    return;
  }
});

const startEditing = (record) => {
  fillForm(record);
};

searchInput.addEventListener("input", () => {
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  searchTimer = setTimeout(() => {
    loadProperties(searchInput.value.trim());
  }, 360);
});

refreshButton.addEventListener("click", () => {
  loadProperties(searchInput.value.trim());
});

loadProperties();
