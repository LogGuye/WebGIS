const metaScript = document.getElementById("adminMeta");
if (!metaScript) {
  throw new Error("Không tìm thấy dữ liệu meta cho admin console.");
}

const adminMeta = JSON.parse(metaScript.textContent || "{}");
const tabsContainer = document.getElementById("adminTabs");
const tableHead = document.querySelector("[data-admin='table-head']");
const tableBody = document.querySelector("[data-admin='table-body']");
const tableEmpty = document.querySelector("[data-admin='empty']");
const entityLabel = document.querySelector("[data-admin='entityLabel']");
const entityDescription = document.querySelector("[data-admin='entityDescription']");
const form = document.getElementById("adminEntityForm");
const formFields = document.querySelector("[data-admin='form-fields']");
const formTitle = document.querySelector("[data-admin='form-title']");
const formDescription = document.querySelector("[data-admin='form-description']");
const formResetBtn = document.querySelector("[data-admin='form-reset']");
const formDeleteBtn = document.querySelector("[data-admin='form-delete']");
const toastEl = document.querySelector("[data-admin='toast']");
let activeEntity = adminMeta.entities?.[0] || null;
let items = [];
let editingId = null;

// Utility functions for cookies and CSRF token retrieval
const getCookie = (name) => {
  if (!document.cookie) return null;
  const cookies = document.cookie.split("; ");
  for (let cookie of cookies) {
    const [key, value] = cookie.split("=");
    if (key === name) return decodeURIComponent(value);
  }
  return null;
};

const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || getCookie("csrftoken");

// Log CSRF token state for debugging purposes
const logCsrfState = () => {
  console.debug("[admin-console] CSRF state", {
    csrfToken,
    cookieToken: getCookie("csrftoken"),
    tokensMatch: getCookie("csrftoken") === csrfToken,
  });
};

// Extract error details from the response to display helpful messages
const extractErrorDetail = async (response) => {
  const data = await response.json().catch(() => ({}));
  const detail = data.error || data.detail || response.statusText || "Đã có lỗi xảy ra.";
  if (response.status === 403) {
    console.warn("[admin-console] CSRF error", detail);
  }
  return detail;
};

// Display toast messages with success or error types
const showToast = (message, variant = "success") => {
  if (!toastEl) return;
  toastEl.textContent = message;
  toastEl.className = `admin-console-toast ${variant} active`;
  setTimeout(() => {
    toastEl.classList.remove("active", "success", "error");
  }, 3500);
};

// Render tabs dynamically based on entities defined in adminMeta
const renderTabs = () => {
  if (!tabsContainer || !adminMeta.entities) return;
  tabsContainer.innerHTML = "";
  adminMeta.entities.forEach((entity) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "admin-console-tab";
    btn.textContent = entity.label;
    btn.dataset.entityKey = entity.key;
    if (activeEntity && entity.key === activeEntity.key) {
      btn.classList.add("active");
    }
    btn.addEventListener("click", () => switchEntity(entity.key));
    tabsContainer.appendChild(btn);
  });
};

// Get metadata for the selected entity
const getEntityMeta = (key) => adminMeta.entities?.find((entity) => entity.key === key) || null;

// Switch the active entity and re-render related components
const switchEntity = (key) => {
  const entity = getEntityMeta(key);
  if (!entity) return;
  activeEntity = entity;
  editingId = null;
  renderTabs();
  renderFormFields();
  entityLabel.textContent = entity.label;
  entityDescription.textContent = entity.description || "";
  formDeleteBtn.style.display = "none";
  formTitle.textContent = `Tạo mới ${entity.label}`;
  formDescription.textContent = entity.description || "";
  fetchList();
};

// Fetch and render the list of records for the active entity
const fetchList = async () => {
  if (!activeEntity) return;
  tableBody.innerHTML = "";
  tableHead.innerHTML = "";
  tableEmpty.textContent = "Đang tải dữ liệu...";
  tableEmpty.style.display = "block";
  try {
    const response = await fetch(activeEntity.endpoints.collection, {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    });
    if (!response.ok) throw new Error("Không thể tải dữ liệu.");
    const payload = await response.json();
    items = payload.results || payload;
    renderTable();
  } catch (error) {
    showToast(error.message, "error");
    tableEmpty.textContent = "Không thể tải dữ liệu.";
  }
};

// Render the table of records for the active entity
const renderTable = () => {
  if (!activeEntity) return;
  const columns = activeEntity.columns || [];
  tableHead.innerHTML = columns.map((col) => `<th>${col.label}</th>`).join("") + "<th></th>";
  if (!items.length) {
    tableBody.innerHTML = "";
    tableEmpty.textContent = "Không có bản ghi nào.";
    tableEmpty.style.display = "block";
    return;
  }
  tableEmpty.style.display = "none";
  tableBody.innerHTML = items
    .map((item) => {
      const cells = columns.map((col) => {
        let value = resolveField(item, col.key);
        if (value === null || value === undefined) value = "—";
        if (col.map && adminMeta.maps && adminMeta.maps[col.map]) {
          value = adminMeta.maps[col.map][String(value)] || value;
        }
        return `<td>${value}</td>`;
      }).join("");
      return `
        <tr data-id="${item.id}">
          ${cells}
          <td class="text-end" style="white-space:nowrap">
            <button type="button" class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${item.id}">Sửa</button>
            <button type="button" class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${item.id}">Xóa</button>
          </td>
        </tr>
      `;
    })
    .join("");
};

// Resolve a nested field from an object
const resolveField = (item, path) => {
  return path.split(".").reduce((acc, key) => acc?.[key], item) ?? null;
};

// Render form fields dynamically based on entity metadata
const renderFormFields = () => {
  if (!activeEntity) return;
  formFields.innerHTML = "";
  (activeEntity.fields || []).forEach((field) => {
    const wrapper = document.createElement("div");
    wrapper.className = "form-field";
    const label = document.createElement("label");
    label.textContent = field.label;
    let input;
    if (field.type === "textarea") {
      input = document.createElement("textarea");
    } else if (field.type === "select") {
      input = document.createElement("select");
      (field.options || []).forEach((option) => {
        const opt = document.createElement("option");
        opt.value = option.value;
        opt.textContent = option.label;
        input.appendChild(opt);
      });
    } else if (field.type === "checkbox") {
      input = document.createElement("input");
      input.type = "checkbox";
    } else {
      input = document.createElement("input");
      input.type = field.type || "text";
    }
    input.name = field.name;
    if (field.placeholder) input.placeholder = field.placeholder;
    if (field.required) input.required = true;
    if (field.step) input.step = field.step;
    label.appendChild(input);
    wrapper.appendChild(label);
    formFields.appendChild(wrapper);
  });
};

// Reset the form state
const resetForm = (silent = false) => {
  editingId = null;
  form.reset();
  formDeleteBtn.style.display = "none";
  formTitle.textContent = `Tạo mới ${activeEntity?.label || "bản ghi"}`;
  if (!silent) showToast("Đã đặt lại form", "success");
};

// Fill the form with data when editing an existing record
const fillForm = (record) => {
  if (!record || !activeEntity) return;
  editingId = record.id;
  formDeleteBtn.style.display = "inline-flex";
  formTitle.textContent = `Cập nhật ${activeEntity.label} #${record.id}`;
  activeEntity.fields.forEach((field) => {
    const input = form.querySelector(`[name="${field.name}"]`);
    if (!input) return;
    const value = record[field.name] !== undefined ? record[field.name] : record[field.name.replace("_id", "")];
    if (field.type === "checkbox") {
      input.checked = Boolean(value);
    } else {
      input.value = value ?? "";
    }
  });
};

// Serialize form data for submission
const serializeForm = () => {
  const data = {};
  activeEntity.fields.forEach((field) => {
    const input = form.querySelector(`[name="${field.name}"]`);
    if (!input) return;
    data[field.name] = field.type === "checkbox" ? input.checked : input.value;
  });
  return data;
};

// Handle form submission (create/update)
const handleSubmit = async (event) => {
  event.preventDefault();
  if (!activeEntity) return;
  const payload = serializeForm();
  const method = editingId ? "PUT" : "POST";
  const url = editingId ? `${activeEntity.endpoints.detail}${editingId}/` : activeEntity.endpoints.collection;
  try {
    logCsrfState();
    const response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-CSRFToken": csrfToken,
      },
      credentials: "same-origin",
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const detail = await extractErrorDetail(response);
      throw new Error(detail);
    }
    await response.json().catch(() => ({}));
    showToast(editingId ? "Đã cập nhật." : "Đã tạo bản ghi.");
    resetForm(true);
    fetchList();
  } catch (error) {
    showToast(error.message, "error");
  }
};

// Handle record deletion
const handleDelete = async () => {
  if (!editingId || !activeEntity) return;
  if (!confirm("Xác nhận xóa bản ghi này?")) return;
  try {
    logCsrfState();
    const response = await fetch(`${activeEntity.endpoints.detail}${editingId}/`, {
      method: "DELETE",
      headers: {
        Accept: "application/json",
        "X-CSRFToken": csrfToken,
      },
      credentials: "same-origin",
    });
    if (!response.ok) {
      const detail = await extractErrorDetail(response);
      throw new Error(detail);
    }
    showToast("Đã xóa.");
    resetForm(true);
    fetchList();
  } catch (error) {
    showToast(error.message, "error");
  }
};

// Event listeners for form actions
form.addEventListener("submit", handleSubmit);
formResetBtn?.addEventListener("click", (event) => {
  event.preventDefault();
  resetForm(true);
});
formDeleteBtn?.addEventListener("click", (event) => {
  event.preventDefault();
  handleDelete();
});
tableBody.addEventListener("click", (event) => {
  const action = event.target.dataset.action;
  const row = event.target.closest("tr");
  if (!row || !action) return;
  const id = row.dataset.id;
  const record = items.find((item) => item.id === Number(id));
  if (action === "edit") {
    fillForm(record);
  } else if (action === "delete") {
    editingId = Number(id);
    handleDelete();
  }
});

// Initial setup
renderTabs();
switchEntity(activeEntity?.key);